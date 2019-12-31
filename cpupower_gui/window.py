# window.py
#
# Copyright 2019 Evangelos Rigas
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


@Gtk.Template(resource_path="/org/rnd2/cpupower_gui/window.glade")
class CpupowerGuiWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "CpupowerGuiWindow"

    cpu_box = Gtk.Template.Child()
    status = Gtk.Template.Child()
    gov_box = Gtk.Template.Child()
    adj_min = Gtk.Template.Child()
    adj_max = Gtk.Template.Child()
    apply_btn = Gtk.Template.Child()
    toall = Gtk.Template.Child()
    about_dialog = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.update_cpubox()
        self._read_settings(self._get_active_cpu())

        self.upd_sliders()
        self.status_icon = self.status
        self.status_icon.connect("popup-menu", self.right_click_event)
        self.status_icon.connect("activate", self.status_activate)

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

    def right_click_event(self, icon, button, time):
        """Handler for right click action on status icon """
        self.menu = Gtk.Menu()
        about = Gtk.MenuItem()
        about.set_label("About")
        about.connect("activate", self.on_about_clicked)
        self.menu.append(about)
        quit = Gtk.MenuItem()
        quit.set_label("Quit")
        quit.connect("activate", self.quit)
        self.menu.append(quit)
        self.menu.show_all()
        self.menu.popup(None, None, None, self.status_icon, button, time)

    def status_activate(self, status_icon):
        """Open window from status icon """
        self.deiconify()
        self.present()

    def quit(self, *args):
        """Quit """
        # HELPER.quit()
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
        fmin = int(self.adj_min.get_value() * 1000)
        fmax = int(self.adj_max.get_value() * 1000)
        cpu = self._get_active_cpu()
        ret = -1
        if HELPER.isauthorized():
            if self.toall.get_active():
                for i in self.online_cpus:
                    ret = HELPER.update_cpu_settings(i, fmin, fmax, self.governor)
            else:
                if self.is_online(cpu):
                    ret = HELPER.update_cpu_settings(cpu, fmin, fmax, self.governor)
                else:
                    error_message("The CPU you selected is not online.", self)
                    self.update_cpubox()
                    return

            if ret == 0:
                button.set_sensitive(False)
            else:
                error_message(
                    "Error occurred, check if you have permissions.", self
                )
        else:
            error_message(
                "You don't have permissions to update cpu settings!", self
            )

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
        if self.is_online(cpu):
            self.freq_min_hw, self.freq_max_hw = HELPER.get_cpu_limits(cpu)
            self.governor = HELPER.get_cpu_governor(cpu)
            self.governors = {}
            for i, gov in enumerate(HELPER.get_cpu_governors(cpu)):
                self.governors[i] = gov
        else:
            error_message("The CPU you selected is not online.", self)
            self.update_cpubox()
            self._read_settings(self._get_active_cpu())

    @property
    def online_cpus(self):
        return HELPER.get_cpus_available()

    @staticmethod
    def is_online(cpu):
        online = HELPER.get_cpus_online()
        present = HELPER.get_cpus_present()
        return (cpu in present) and (cpu in online)
