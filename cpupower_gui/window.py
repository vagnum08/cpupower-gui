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
from .config import CpuPowerConfig
from .utils import read_available_frequencies

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
    gov_container = Gtk.Template.Child()
    profile_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Read configuration
        self.conf = CpuPowerConfig()
        # Get GUI config and profiles
        self.gui_conf = self.conf.get_gui_settings()
        self.profiles = self.conf.profiles
        self.profile = None

        self.conf_store = {}
        self.refreshing = False
        self.update_cpubox()
        self.init_conf_store()
        self.configure_gui()
        self.upd_sliders()

        # Application actions
        action = Gio.SimpleAction.new("Exit", None)
        action.connect("activate", self.quit)
        self.add_action(action)

    def init_conf_store(self):
        """Initialise the configuration store"""
        for cpu in self.online_cpus:
            self._update_cpu_conf(int(cpu))
            self._update_cpu_foreground(int(cpu), False)

    def update_cpubox(self):
        """Update the CPU Combobox"""
        self.cpu_store = Gtk.ListStore(int, str)
        self.cpu_box.set_model(self.cpu_store)
        # Get cell renderer
        cells = self.cpu_box.get_cells()
        if cells:
            cell = cells[0]
            # Change foreground based on second column of cpu_store
            # If the cpu settings are changed then cpu text is coloured red
            self.cpu_box.add_attribute(cell, "foreground", 1)

        for cpu in self.online_cpus:
            self.cpu_store.append([cpu, "black"])

        self.cpu_box.set_active(0)

    def configure_gui(self):
        """Configures GUI based on the config file"""
        # To all cpus toggle
        toggle_default = self.gui_conf.getboolean("allcpus_default", False)
        self.toall.set_active(toggle_default)

        # Configure profiles box
        self.prof_store = Gtk.ListStore(str)
        self.profile_box.set_model(self.prof_store)

        # Empty profile name to use for resetting settings
        self.prof_store.append([""])

        # Add the profiles from configuration
        for prof in self.profiles:
            self.prof_store.append([prof])

    def quit(self, *args):
        """Quit"""
        HELPER.quit()
        exit(0)

    def _update_cpu_conf(self, cpu):
        """Update the configuration store (dict) for cpu

        Args:
            cpu: Index number of cpu

        """
        # Initialise temporary config dictionary
        confd = {
            "hw_lims": (None, None),
            "freqs": (None, None),
            "online": None,
            "governor": None,
            "governors": [],
            "changed": False,
        }

        # Gather values
        hw_min, hw_max = HELPER.get_cpu_limits(cpu)
        confd["hw_lims"] = (int(hw_min), int(hw_max))

        fmin, fmax = HELPER.get_cpu_frequencies(cpu)
        confd["freqs"] = (int(fmin), int(fmax))

        confd["online"] = self.is_online(cpu)

        gov_conf = self._update_gov_conf(cpu)
        confd["governor"] = gov_conf[0]
        confd["governors"] = gov_conf[1]

        # Store settings
        self.conf_store.update({cpu: confd})

    def _update_gov_conf(self, cpu: int):
        """Helper function to get governor settings

        Args:
            cpu: The cpu core to update

        Returns:
            govid: Index of the current governor
            governors: A list with the available governors

        """
        governor = str(HELPER.get_cpu_governor(cpu))
        if governor == "ERROR":
            govid = None
            governors = []
        else:
            governors = self.get_cpu_governors(cpu)
            if governor in governors:
                govid = governors.index(governor)
            else:
                govid = None

        return govid, governors

    def _update_conf_store_freqs(self, cpu, fmin, fmax):
        """Updates conf_store frequency values for `cpu`

        Args:
            cpu: Index of cpu to update
            fmin: Minimum scaling frequency
            fmax: Minimum scaling frequency

        """
        conf = self.conf_store.get(cpu)
        if conf is not None:
            conf.update({"freqs": (fmin * 1000, fmax * 1000), "changed": True})
        self._update_cpu_foreground(cpu, True)

    def _update_conf_store_online(self, cpu, online):
        """Updates conf_store online value for `cpu`

        Args:
            cpu: Index of cpu to update
            online: Boolean indication if cpu is online or offline

        """
        conf = self.conf_store.get(cpu)
        changed = True if online != self.is_online(cpu) else False

        if conf is not None:
            conf["online"] = online
            if changed:
                conf["changed"] = True
        self._update_cpu_foreground(cpu, True)

    def _update_cpu_foreground(self, cpu, changed):
        """Change colour on the combobox if cpu settings were changed

        Args:
            cpu: Index of cpu to update
            changed: If changed is True, cpu text will be coloured red,
             otherwise the text will be black

        """
        color = "red" if changed else "black"
        if cpu <= len(self.cpu_store):
            self.cpu_store[cpu][1] = color

    def upd_sliders(self, refresh=False):
        """Updates the slider widgets by reading the sys files

        Args:
            refresh: If refresh is True, it resets the sliders to the values
             as read from the hardware

        """
        cpu = self._get_active_cpu()
        conf = self.conf_store.get(cpu)
        if not conf:
            return

        freq_min_hw, freq_max_hw = conf.get("hw_lims")
        if refresh:
            cpu_online = self.is_online(cpu)
            freq_min, freq_max = HELPER.get_cpu_frequencies(cpu)
            conf["governor"], conf["governors"] = self._update_gov_conf(cpu)
            conf["changed"] = False  # Reset changed status for cpu
        else:
            cpu_online = conf.get("online")
            freq_min, freq_max = conf.get("freqs")

        governor = conf.get("governor")
        governors = conf.get("governors")

        self.refreshing = True  # Use the flag to skip callbacks

        if governor is not None:
            gov_store = Gtk.ListStore(str, int)
            for govid, gov in enumerate(governors):
                gov_store.append([gov.capitalize(), govid])

            self.gov_box.set_model(gov_store)
            self.gov_box.set_active(governor)
            self.gov_container.set_sensitive(True)
        else:
            self.gov_container.set_sensitive(False)

        # Update sliders
        self._set_sliders_sensitive(cpu_online)
        self._update_frequency_marks(cpu)
        self.adj_min.set_lower(int(freq_min_hw / 1000))
        self.adj_min.set_upper(int(freq_max_hw / 1000))
        self.adj_max.set_lower(int(freq_min_hw / 1000))
        self.adj_max.set_upper(int(freq_max_hw / 1000))
        self.adj_min.set_value(int(freq_min / 1000))
        self.adj_max.set_value(int(freq_max / 1000))
        self.apply_btn.set_sensitive(self.is_conf_changed)
        self.cpu_online.set_active(cpu_online)
        self.cpu_online.set_sensitive(bool(HELPER.cpu_allowed_offline(cpu)))
        self.refreshing = False  # Now the callbacks work normally
        self._update_cpu_foreground(cpu, conf["changed"])

    def _get_active_cpu(self):
        """Helper function to get cpu from combobox"""
        cpu_iter = self.cpu_box.get_active_iter()
        if cpu_iter is not None:
            return int(self.cpu_store[cpu_iter][0])

        self.update_cpubox()
        return 0

    def _set_profile_settings(self, profile):
        """Set the settings based on the selected profile"""
        self.init_conf_store()  # Discard any changes

        # If no profile selected reset and disable apply_btn
        if profile == "":
            return False

        prof_settings = self.conf.get_profile_settings(profile)
        for cpu, settings in prof_settings.items():
            cpu_conf = self.conf_store.get(cpu)
            if not cpu_conf:
                continue
            cpu_conf["freqs"] = settings["freqs"]
            if settings["governor"] in cpu_conf["governors"]:
                govid = cpu_conf["governors"].index(settings["governor"])
                cpu_conf["governor"] = govid
            cpu_conf["online"] = settings["online"]
            cpu_conf["changed"] = True
            self._update_cpu_foreground(cpu, True)
        return True

    def _set_sliders_sensitive(self, state):
        """Enable/Disable sliders and combo boxes"""
        self.spin_min.set_sensitive(state)
        self.spin_max.set_sensitive(state)
        self.min_sl.set_sensitive(state)
        self.max_sl.set_sensitive(state)
        self.gov_container.set_sensitive(state)

    def _update_frequency_marks(self, cpu):
        """Add or remove slider marks for frequency steps

        Args:
            cpu: Index of cpu to query

        """
        # Clear marks
        self.min_sl.clear_marks()
        self.max_sl.clear_marks()

        steps = self.get_cpu_frequency_steps(cpu)
        if not steps:
            return

        markup = "{:1.1f} GHz"
        for frequency in steps:
            freq = float(frequency / 1e3)
            mark = markup.format(freq)
            self.min_sl.add_mark(frequency, Gtk.PositionType.TOP, mark)
            self.max_sl.add_mark(frequency, Gtk.PositionType.TOP)

    @Gtk.Template.Callback()
    def on_cpu_changed(self, *args):
        """Callback for cpu box"""
        # pylint: disable=W0612,W0613
        self.upd_sliders()

    @Gtk.Template.Callback()
    def on_toall_state_set(self, _, val):
        """Enable/Disable cpu_box"""
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
        """Callback for adj_min"""
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        cpu = self._get_active_cpu()
        fmin = self.adj_min.get_value()
        fmax = self.adj_max.get_value()
        fmin_hw, fmax_hw = self.conf_store[cpu].get("hw_lims")

        if fmin > fmax:
            if fmin + 10 > fmax_hw / 1000:
                self.adj_max.set_value(fmax_hw / 1000)
            else:
                self.adj_max.set_value(fmin + 10)
        elif fmax < fmin:
            if fmax - 10 < fmin_hw / 1000:
                self.adj_min.set_value(fmin_hw / 1000)
            else:
                self.adj_min.set_value(fmax - 10)

        self._update_conf_store_freqs(cpu, fmin, fmax)
        self.apply_btn.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_adj_max_value_changed(self, *args):
        """Callback for adj_max"""
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        cpu = self._get_active_cpu()
        fmin = self.adj_min.get_value()
        fmax = self.adj_max.get_value()

        if fmax < fmin:
            self.adj_min.set_value(fmax - 10)

        self._update_conf_store_freqs(cpu, fmin, fmax)
        self.apply_btn.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_refresh_clicked(self, *args):
        """Callback for refresh button"""
        self.upd_sliders(refresh=True)

    @Gtk.Template.Callback()
    def on_cpu_online_toggled(self, *args):
        """Callback for cpu_online toggle"""
        if self.refreshing:
            return
        cpu = self._get_active_cpu()
        chk = self.cpu_online.get_active()
        changed = self.is_online(cpu) ^ chk
        tgl = self.apply_btn.get_sensitive() or changed
        self._set_sliders_sensitive(chk)
        self.apply_btn.set_sensitive(tgl)
        self._update_conf_store_online(cpu, chk)

    @Gtk.Template.Callback()
    def on_governor_changed(self, *args):
        """Callback for governor combobox
        Change governor and enable apply_btn
        """
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        mod = self.gov_box.get_model()
        text, tid = mod[self.gov_box.get_active_iter()][:2]
        # Update store
        cpu = self._get_active_cpu()
        conf = self.conf_store.get(cpu)
        conf["governor"] = tid
        conf["changed"] = True
        self.apply_btn.set_sensitive(True)
        self._update_cpu_foreground(cpu, True)

    @Gtk.Template.Callback()
    def on_profile_changed(self, *args):
        """Callback for profile combobox
        Change profile and enable apply_btn
        """
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        mod = self.profile_box.get_model()
        profile = mod[self.profile_box.get_active_iter()][0]
        # Update store
        res = self._set_profile_settings(profile)
        self.toall.set_active(False) # Disable toggle
        self.upd_sliders()
        self.apply_btn.set_sensitive(res)

    @Gtk.Template.Callback()
    def on_apply_clicked(self, button):
        """Write changes back to sysfs"""
        ret = -1

        if HELPER.isauthorized():
            # If toall is toggle update all cores with the same settings
            if self.toall.get_active():
                for cpu in self.online_cpus:
                    self.set_cpu_online(cpu)
                    if self.is_online(cpu):
                        ret = HELPER.update_cpu_settings(cpu, self.fmin, self.fmax)
                        ret += self.set_cpu_governor(cpu)
            else:
                # Update only the cpus whose settings were changed
                changed_cpus = [
                    cpu for cpu, conf in self.conf_store.items() if conf.get("changed")
                ]
                if not changed_cpus:
                    return

                for cpu in changed_cpus:
                    conf = self.conf_store.get(cpu)
                    cpu_online = conf.get("online")
                    ret = self.set_cpu_online(cpu)
                    if cpu_online:
                        ret += self.set_cpu_frequencies(cpu)
                        ret += self.set_cpu_governor(cpu)
                    conf["changed"] = False
                    self._update_cpu_foreground(cpu, False)

            # Update sliders
            self.profile_box.set_active(0)
            self.init_conf_store()
            self.upd_sliders()

            if ret == 0:
                button.set_sensitive(False)
            else:
                error_message("Error occurred, check if you have permissions.", self)
        else:
            error_message("You don't have permissions to update cpu settings!", self)

    @Gtk.Template.Callback()
    def on_about_clicked(self, button):
        """Callback for about"""
        self.show_about_dialog()

    def show_about_dialog(self):
        """Shows the about dialog"""
        self.about_dialog.run()
        self.about_dialog.hide()

    @property
    def fmin(self):
        """Convenience function to return minimum frequency"""
        return int(self.adj_min.get_value() * 1000)

    @property
    def fmax(self):
        """Convenience function to return maximum frequency"""
        return int(self.adj_max.get_value() * 1000)

    @property
    def online_cpus(self):
        """Convenience function to get a list of available CPUs"""
        return HELPER.get_cpus_available()

    @property
    def is_conf_changed(self):
        """Helper function to check if settings were changed"""
        changed = [cpu for cpu, conf in self.conf_store.items() if conf["changed"]]
        return len(changed) > 0

    @staticmethod
    def is_online(cpu):
        """Wrapper to get the online state for a cpu

        Args:
            cpu: Index of cpu to query

        Returns:
            bool: True if cpu is online, false otherwise

        """

        online = HELPER.get_cpus_online()
        present = HELPER.get_cpus_present()
        return (cpu in present) and (cpu in online)

    @staticmethod
    def is_offline(cpu):
        """Wrapper to get the online state for a cpu

        Args:
            cpu: Index of cpu to query

        Returns:
            bool: True if cpu is offline, false otherwise

        """
        offline = HELPER.get_cpus_offline()
        present = HELPER.get_cpus_present()
        return (cpu in present) and (cpu in offline)

    @staticmethod
    def get_cpu_governors(cpu):
        """Wrapper to get the list of available governors for a cpu

        Args:
            cpu: Index of cpu to query

        """
        governors = []
        for gov in HELPER.get_cpu_governors(cpu):
            governors.append(str(gov))

        return governors

    @staticmethod
    def get_cpu_frequency_steps(cpu):
        """Wrapper to get the list of available frequencies

        Args:
            cpu: Index of cpu to query

        """
        frequencies = read_available_frequencies(cpu)
        if not frequencies:
            return []

        # Convert and scale frequencies to MHz
        return [int(freq) / 1e3 for freq in frequencies]

    def set_cpu_online(self, cpu):
        """Sets the online attribute for cpu

        Args:
            cpu: Index of cpu to set

        """
        conf = self.conf_store.get(cpu)
        if conf is None:
            return

        cpu_online = conf.get("online")

        # If cpu is offline, enable and update freq settings
        if self.is_offline(cpu) and cpu_online:
            ret = HELPER.set_cpu_online(cpu)
            self.upd_sliders()
            return ret

        # If cpu is online, disable
        if self.is_online(cpu) and not cpu_online:
            # Set offline only if CPU is allowed to go offline
            if HELPER.cpu_allowed_offline(cpu):
                return HELPER.set_cpu_offline(cpu)

        # No change to the cpu
        return 0

    def set_cpu_governor(self, cpu):
        """Sets the governor for cpu

        Args:
            cpu: Index of cpu to set

        """
        ret = -1
        conf = self.conf_store.get(cpu)
        if conf is None:
            return ret

        govid = conf.get("governor")
        # If govid is None means that there is an error with the kernel
        # https://github.com/vagnum08/cpupower-gui/issues/12
        if govid is None:
            return ret

        govs = conf.get("governors")
        if govs:
            ret = HELPER.update_cpu_governor(cpu, govs[govid])

        return ret

    def set_cpu_frequencies(self, cpu):
        """Sets the frequency limits for cpu

        Args:
            cpu: Index of cpu to set

        """
        ret = -1
        conf = self.conf_store.get(cpu)
        if conf is None:
            return ret

        fmin, fmax = conf.get("freqs")
        if (fmin is not None) and (fmax is not None):
            ret = HELPER.update_cpu_settings(cpu, fmin, fmax)

        return ret
