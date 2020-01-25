# window.py
#
# Copyright 2019-2020 Evangelos Rigas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import dbus

from gi.repository import Gtk, Gio

BUS = dbus.SystemBus()
SESSION = BUS.get_object(
    "org.rnd2.cpupower_gui.helper", "/org/rnd2/cpupower_gui/helper"
)

HELPER = dbus.Interface(SESSION, "org.rnd2.cpupower_gui.helper")


def dialog_response(widget, response_id):
    """ Error message dialog """
    # if the button clicked gives response OK (-5)
    if response_id == Gtk.ResponseType.OK:
        print("OK")
    # if the messagedialog is destroyed (by pressing ESC)
    elif response_id == Gtk.ResponseType.DELETE_EVENT:
        print("dialog closed or cancelled")
    widget.destroy()


def error_message(msg, transient):
    message = Gtk.MessageDialog(type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK)
    message.set_markup(msg)
    message.set_transient_for(transient)
    message.show()
    message.connect("response", dialog_response)


@Gtk.Template(resource_path="/org/rnd2/cpupower_gui/window.ui")
class CpupowerGuiWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "CpupowerGuiWindow"

    cpu_box = Gtk.Template.Child()
    gov_box = Gtk.Template.Child()
    adj_min = Gtk.Template.Child()
    adj_max = Gtk.Template.Child()
    spin_min = Gtk.Template.Child()
    spin_max = Gtk.Template.Child()
    min_sl = Gtk.Template.Child()
    max_sl = Gtk.Template.Child()
    apply_btn = Gtk.Template.Child()
    toall = Gtk.Template.Child()
    about_dialog = Gtk.Template.Child()
    cpu_online = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.update_cpubox()
        self._read_settings(self._get_active_cpu())

        self.upd_sliders()

        # Application actions
        action = Gio.SimpleAction.new("Exit", None)
        action.connect("activate", self.quit)
        self.add_action(action)

    def update_cpubox(self):
        self.cpu_store = Gtk.ListStore(int)

        for cpu in self.online_cpus:
            self.cpu_store.append([cpu])

        self.cpu_box.set_model(self.cpu_store)
        self.cpu_box.set_active(0)

    def quit(self, *args):
        """Quit """
        HELPER.quit()
        exit(0)

    def _get_active_cpu(self):
        iter = self.cpu_box.get_active_iter()
        if iter is not None:
            return int(self.cpu_store[iter][0])

        self.update_cpubox()
        return 0

    def upd_sliders(self):
        """ Updates the slider widgets by reading the sys files"""
        cpu = self._get_active_cpu()

        self._read_settings(cpu)
        freq_min, freq_max = HELPER.get_cpu_frequencies(cpu)

        gov_store = Gtk.ListStore(str, int)
        for gov in self.governors.items():
            if gov[1] == self.governor:
                gov_id = gov[0]
            gov_store.append([gov[1].capitalize(), gov[0]])

        self.gov_box.set_model(gov_store)
        self.gov_box.set_active(gov_id)

        self.adj_min.set_lower(int(self.freq_min_hw / 1000))
        self.adj_min.set_upper(int(self.freq_max_hw / 1000))
        self.adj_max.set_lower(int(self.freq_min_hw / 1000))
        self.adj_max.set_upper(int(self.freq_max_hw / 1000))
        self.adj_min.set_value(int(freq_min / 1000))
        self.adj_max.set_value(int(freq_max / 1000))
        self.apply_btn.set_sensitive(False)
        self.cpu_online.set_active(self.is_online(cpu))
        self.cpu_online.set_sensitive(bool(HELPER.cpu_allowed_offline(cpu)))

    @Gtk.Template.Callback()
    def on_cpu_changed(self, *args):
        """ Callback for cpu box """
        # pylint: disable=W0612,W0613
        self.upd_sliders()

    @Gtk.Template.Callback()
    def on_toall_state_set(self, _, val):
        """ Enable/Disable cpu_box """
        if val:
            self.cpu_box.set_sensitive(False)
        else:
            self.cpu_box.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_atboot_state_set(self, _, val):
        if val:
            self.ATBOOT = True
            print(HELPER.isauthorized())
        else:
            self.ATBOOT = False

    @Gtk.Template.Callback()
    def on_adj_min_value_changed(self, *args):
        """ Callback for adj_min """
        # pylint: disable=W0612,W0613
        if self.adj_min.get_value() > self.adj_max.get_value():
            if self.adj_min.get_value() + 10 > self.freq_max_hw / 1000:
                self.adj_max.set_value(self.freq_max_hw / 1000)
            else:
                self.adj_max.set_value(self.adj_min.get_value() + 10)
        elif self.adj_max.get_value() < self.adj_min.get_value():
            if self.adj_max.get_value() - 10 < self.freq_min_hw / 1000:
                self.adj_min.set_value(self.freq_min_hw / 1000)
            else:
                self.adj_min.set_value(self.adj_max.get_value() - 10)
        self.apply_btn.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_adj_max_value_changed(self, *args):
        """ Callback for adj_max """
        # pylint: disable=W0612,W0613
        if self.adj_max.get_value() < self.adj_min.get_value():
            self.adj_min.set_value(self.adj_max.get_value() - 10)
        self.apply_btn.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_refresh_clicked(self, *args):
        self.upd_sliders()

    @Gtk.Template.Callback()
    def on_cpu_online_toggled(self, *args):
        cpu = self._get_active_cpu()
        chk = self.cpu_online.get_active()
        changed = self.is_online(cpu) ^ chk
        tgl = self.apply_btn.get_sensitive() or changed
        self.apply_btn.set_sensitive(tgl)
        self.spin_min.set_sensitive(chk)
        self.spin_max.set_sensitive(chk)
        self.min_sl.set_sensitive(chk)
        self.max_sl.set_sensitive(chk)

    @Gtk.Template.Callback()
    def on_governor_changed(self, *args):
        """ Change governor and enable apply_btn """
        # pylint: disable=W0612,W0613
        mod = self.gov_box.get_model()
        text, tid = mod[self.gov_box.get_active_iter()][:2]
        self.governor = self.governors[tid]
        self.apply_btn.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_apply_clicked(self, button):
        """ Write changes back to sysfs """
        cpu = self._get_active_cpu()
        ret = -1
        if HELPER.isauthorized():
            if self.toall.get_active():
                for i in self.online_cpus:
                    self.set_cpu_online(i)
                    if self.is_online(cpu):
                        ret = HELPER.update_cpu_settings(
                            i, self.fmin, self.fmax, self.governor
                        )
            else:
                ret = self.set_cpu_online(cpu)
                if self.cpu_online.get_active():
                    ret = HELPER.update_cpu_settings(
                        cpu, self.fmin, self.fmax, self.governor
                    )

            # Update sliders
            self.upd_sliders()

            if ret == 0:
                button.set_sensitive(False)
            else:
                error_message("Error occurred, check if you have permissions.", self)
        else:
            error_message("You don't have permissions to update cpu settings!", self)

    @Gtk.Template.Callback()
    def on_about_clicked(self, button):
        self.show_about_dialog()

    def show_about_dialog(self):
        self.about_dialog.run()
        self.about_dialog.hide()

    @Gtk.Template.Callback()
    def on_config_box_changed(self, button):
        self.about_dialog.hide()

    def _read_settings(self, cpu):
        self.freq_min_hw, self.freq_max_hw = HELPER.get_cpu_limits(cpu)
        self.governor = HELPER.get_cpu_governor(cpu)
        self.governors = {}
        for i, gov in enumerate(HELPER.get_cpu_governors(cpu)):
            self.governors[i] = gov

    @property
    def fmin(self):
        return int(self.adj_min.get_value() * 1000)

    @property
    def fmax(self):
        return int(self.adj_max.get_value() * 1000)

    @property
    def online_cpus(self):
        return HELPER.get_cpus_available()

    @staticmethod
    def is_online(cpu):
        online = HELPER.get_cpus_online()
        present = HELPER.get_cpus_present()
        return (cpu in present) and (cpu in online)

    @staticmethod
    def is_offline(cpu):
        offline = HELPER.get_cpus_offline()
        present = HELPER.get_cpus_present()
        return (cpu in present) and (cpu in offline)

    def set_cpu_online(self, cpu):
        # If cpu is offline, enable and update freq settings
        if self.is_offline(cpu) and self.cpu_online.get_active():
            ret = HELPER.set_cpu_online(cpu)
            self.upd_sliders()
            return ret

        # If cpu is online, disable
        if self.is_online(cpu) and not self.cpu_online.get_active():
            if HELPER.cpu_allowed_offline(cpu):
                return HELPER.set_cpu_offline(cpu)

        # No change to the cpu
        return 0
