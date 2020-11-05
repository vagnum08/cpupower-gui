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

from contextlib import contextmanager
from gettext import gettext as _

import dbus
import gi

gi.require_version("Handy", "1")

from gi.repository import Gio, GLib, GObject, Gtk, Handy

from .config import CpuPowerConfig, CpuSettings
from .utils import read_available_frequencies, read_current_freq

BUS = dbus.SystemBus()
SESSION = BUS.get_object(
    "org.rnd2.cpupower_gui.helper", "/org/rnd2/cpupower_gui/helper"
)

HELPER = dbus.Interface(SESSION, "org.rnd2.cpupower_gui.helper")

ERRORS = {
    -11: "Setting governor failed.",
    -12: "Setting energy preferences failed.",
    -13: "Setting frequencies failed.",
    -23: "Setting governor and energy preferences failed.",
    -24: "Setting governor and frequencies failed.",
    -25: "Setting frequencies and energy preferences failed.",
}

# Abstractions for Gio List store
class CpuCore(GObject.GObject):

    name = GObject.Property(type=str)

    def __init__(self, name):
        GObject.GObject.__init__(self)
        self.name = name


class EnergyPref(GObject.GObject):

    prefid = GObject.Property(type=int)
    name = GObject.Property(type=str)

    def __init__(self, prefid, name):
        GObject.GObject.__init__(self)
        self.prefid = prefid
        self.name = name


class Governor(GObject.GObject):

    govid = GObject.Property(type=int)
    name = GObject.Property(type=str)

    def __init__(self, govid, name):
        GObject.GObject.__init__(self)
        self.govid = govid
        self.name = name


class Profile(GObject.GObject):

    name = GObject.Property(type=str)

    def __init__(self, profile):
        GObject.GObject.__init__(self)

        if isinstance(profile, str):
            self._profile = None
            self.name = profile
            return

        self._profile = profile
        self.name = profile.name

        if not profile._custom:
            self.name += " (Built-in)"

    @property
    def settings(self):
        if self._profile:
            return self._profile.settings
        else:
            return []


def dialog_response(widget, response_id):
    """ Error message dialog """
    # if the button clicked gives response OK (-5)
    # if response_id == Gtk.ResponseType.OK:
    #    print("OK")
    # if the messagedialog is destroyed (by pressing ESC)
    # elif response_id == Gtk.ResponseType.DELETE_EVENT:
    #    print("dialog closed or cancelled")
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

    Handy.init()
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
    profile_box = Gtk.Template.Child()
    default_profile_pref = Gtk.Template.Child()
    energy_pref_box = Gtk.Template.Child()
    tree_view = Gtk.Template.Child()
    headerbar_switcher = Gtk.Template.Child()
    bottom_switcher = Gtk.Template.Child()
    squeezer = Gtk.Template.Child()
    default_allcpus = Gtk.Template.Child()
    default_ticks = Gtk.Template.Child()
    default_ticks_num = Gtk.Template.Child()
    default_energy_per_cpu = Gtk.Template.Child()
    energy_pref_percpu = Gtk.Template.Child()
    profile_overview = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.squeezer.connect(
            "notify::visible-child", self.on_headerbar_squeezer_notify
        )
        # Read configuration
        self.conf = CpuPowerConfig()
        # Get GUI config and profiles
        self.gui_conf = self.conf.get_gui_settings()
        self.profiles = self.conf.profiles
        self.profile = None

        self.refreshing = False
        self.settings = {}
        self.energy_pref_avail = False
        self.energy_per_cpu = False
        self.tree_store = None
        self.tick_marks_enabled = True
        self.ticks_markup = True
        self.selected_cpus = None

        self.style_ctx = self.tree_view.get_style_context()
        self.fg = self.style_ctx.get_color(Gtk.StateFlags.NORMAL).to_string()
        self.update_cpubox()
        self.load_cpu_settings()
        self._update_tree_view()
        self.configure_gui()
        self.upd_sliders()

        GLib.timeout_add(500, self._update_current_freq)
        # Application actions
        action = Gio.SimpleAction.new("Exit", None)
        action.connect("activate", self.quit)
        self.add_action(action)

    def on_headerbar_squeezer_notify(self, squeezer, event):
        child = squeezer.get_visible_child()
        self.bottom_switcher.set_reveal(child != self.headerbar_switcher)
        self.gov_box.set_use_subtitle(child != self.headerbar_switcher)
        self.energy_pref_box.set_use_subtitle(child != self.headerbar_switcher)
        self.cpu_box.set_use_subtitle(child != self.headerbar_switcher)

    @contextmanager
    def lock(self):
        """Helper function to stop widgets from refreshing"""
        self.refreshing = True
        yield
        self.refreshing = False

    def load_cpu_settings(self):
        """Initialise the configuration store"""
        for cpu in self.online_cpus:
            self.settings[cpu] = CpuSettings(cpu)
            self._update_treeview_style(cpu, False)
        self.energy_pref_avail = self.settings[0].energy_pref_avail

    def update_cpubox(self):
        """Update the CPU Combobox"""
        self.cpu_store = Gio.ListStore()
        self.cpu_box.bind_name_model(self.cpu_store, lambda x: x.name)

        for cpu in self.online_cpus:
            self.cpu_store.append(CpuCore(cpu))

        self.cpu_box.set_selected_index(0)

    def configure_gui(self):
        """Configures GUI based on the config file"""

        # Add prefix checkbutton to cpu
        self.cpu_online = Gtk.CheckButton()
        self.cpu_online.connect("toggled", self.on_cpu_online_toggled)
        self.cpu_box.add_prefix(self.cpu_online)
        self.cpu_online.show()

        # Preferences
        toggle_default = self.gui_conf.getboolean("allcpus_default", False)
        self.toall.set_active(toggle_default)
        self.default_allcpus.set_active(toggle_default)

        default_ticks = self.gui_conf.getboolean("tick_marks_enabled", True)
        self.tick_marks_enabled = default_ticks
        self.default_ticks.set_active(default_ticks)

        default_ticks_num = self.gui_conf.getboolean("frequency_ticks", True)
        self.ticks_markup = default_ticks_num
        self.default_ticks_num.set_active(default_ticks_num)

        default_energy_percpu = self.gui_conf.getboolean("energy_pref_per_cpu", False)
        self.energy_per_cpu = default_energy_percpu
        self.default_energy_per_cpu.set_active(default_energy_percpu)

        self.update_profile_boxes()

        self.generate_profiles_page()

        # Check if intel pstate perfs are available
        if self.energy_pref_avail:
            self.energy_pref_box.set_visible(True)
            self.energy_pref_percpu.set_visible(True)

    def update_profile_boxes(self):
        # Configure profiles box
        self.prof_store = Gio.ListStore()

        # Empty profile name to use for resetting settings
        self.prof_store.append(Profile(_("No profile")))

        # Add the profiles from configuration
        for prof in self.conf.profiles:
            profile = self.conf.get_profile(prof)
            self.prof_store.append(Profile(profile))

        self.profile_box.bind_name_model(self.prof_store, lambda x: x.name)

        # Add the profiles from configuration to prefs
        model = Gio.ListStore()
        for prof in self.conf.profiles:
            model.append(Profile(prof))

        index = self.conf.get_profile_index(self.conf.default_profile)
        self.default_profile_pref.bind_name_model(model, lambda x: x.name)
        self.default_profile_pref.set_selected_index(index)

    def generate_profiles_page(self):
        """Create preference groups for profiles"""
        new_profile = Handy.PreferencesGroup(title=_("New profile"))
        self.custom_profiles = Handy.PreferencesGroup(title=_("User profiles"))
        self.system_profiles = Handy.PreferencesGroup(title=_("System profiles"))
        self.builtin_profiles = Handy.PreferencesGroup(title=_("Built-in profiles"))
        self.profile_overview.add(new_profile)
        self.profile_overview.add(self.custom_profiles)
        self.profile_overview.add(self.system_profiles)
        self.profile_overview.add(self.builtin_profiles)

        # Add entry for current profile
        prof_entry = Handy.ActionRow(title=_("Profile name"))
        save_me = Gtk.Button.new_from_icon_name("document-save", 1)
        save_me.set_sensitive(False)
        self.profile_name_entry = Gtk.Entry(placeholder_text=_("Name"))
        self.profile_name_entry.connect("changed", self.on_prof_name_changed, save_me)
        prof_entry.add(self.profile_name_entry)
        prof_entry.add(save_me)
        save_me.connect("clicked", self.on_save_profile_clicked)
        prof_entry.set_activatable_widget(save_me)
        new_profile.add(prof_entry)

        self._generate_profile_list()

    def update_profiles_page(self):
        """Update listed profiles"""
        for child in self.custom_profiles.get_children():
            child.destroy()
        for child in self.system_profiles.get_children():
            child.destroy()
        for child in self.builtin_profiles.get_children():
            child.destroy()
        self._generate_profile_list()

    def _generate_profile_list(self):
        """Create profile listings using fresh config"""
        # Add entries for saved profiles
        for prof in self.conf.profiles:
            profile = self.conf.get_profile(prof)
            prof_entry = Handy.ActionRow()
            prof_entry.set_title(prof)
            if profile._custom:
                if not profile.system:
                    delete_me = Gtk.Button.new_from_icon_name("edit-delete", 1)
                    prof_entry.add(delete_me)
                    delete_me.connect("clicked", self.on_delete_profile_clicked, prof)
                    prof_entry.set_activatable_widget(delete_me)
                    self.custom_profiles.add(prof_entry)
                else:
                    self.system_profiles.add(prof_entry)
            else:
                self.builtin_profiles.add(prof_entry)

        self.profile_overview.show_all()

    def quit(self, *args):
        """Quit"""
        HELPER.quit()
        exit(0)

    def _reset_energy_conf(self, cpu):
        if cpu == -1:
            # Reset conf for all cpus
            for cpu, conf in self.settings.items():
                conf.reset_energy_pref()
                self._update_treeview_style(cpu, conf.changed)
            return

        self.settings[cpu].reset_energy_pref()

    def _update_settings_freqs(self, cpu, fmin, fmax):
        """Updates settings frequency values for `cpu`

        Args:
            cpu: Index of cpu to update
            fmin: Minimum scaling frequency
            fmax: Minimum scaling frequency

        """
        if self.toall.get_active():
            for cpu, row in enumerate(self.tree_store):
                conf = self.settings.get(cpu)
                if conf is not None:
                    conf.freqs = (fmin, fmax)
                row[2] = fmin
                row[3] = fmax
                self._update_treeview_style(cpu, conf.changed)
        else:
            conf = self.settings.get(cpu)
            if conf is not None:
                conf.freqs = (fmin, fmax)
            self.tree_store[cpu][2] = fmin
            self.tree_store[cpu][3] = fmax
            self._update_treeview_style(cpu, conf.changed)

    def _update_settings_online(self, cpu, online):
        """Updates settings online value for `cpu`

        Args:
            cpu: Index of cpu to update
            online: Boolean indication if cpu is online or offline

        """
        conf = self.settings.get(cpu)

        if conf is not None:
            conf.online = online
        self._update_treeview_style(cpu, conf.changed)

    def _update_treeview_style(self, cpu, changed):
        """Change style on the tree view if cpu settings were changed

        Args:
            cpu: Index of cpu to update
            changed: If changed is True, cpu text will be coloured red,
             otherwise the text will be black

        """
        style = 1 if changed else 0
        if cpu <= len(self.settings):
            if self.tree_store:
                self.tree_store[cpu][6] = style

    def upd_sliders(self):
        """Updates the slider widgets by reading the sys files"""
        cpu = self._get_active_cpu()
        conf = self.settings.get(cpu)
        if not conf:
            return

        freq_min_hw, freq_max_hw = conf.hw_lims
        cpu_online = conf.online
        freq_min, freq_max = conf.freqs

        with self.lock():  # Use the flag to skip callbacks
            self._update_gov_box()
            if self.energy_pref_avail:
                self._update_energy_pref_box()

            # Update sliders
            self._set_sliders_sensitive(cpu_online)
            self._update_frequency_marks(cpu)
            self.adj_min.set_lower(freq_min_hw)
            self.adj_min.set_upper(freq_max_hw)
            self.adj_max.set_lower(freq_min_hw)
            self.adj_max.set_upper(freq_max_hw)
            self.adj_min.set_value(freq_min)
            self.adj_max.set_value(freq_max)

            self.apply_btn.set_sensitive(self.is_conf_changed)
            self.cpu_online.set_active(cpu_online)
            self.cpu_online.set_sensitive(bool(HELPER.cpu_allowed_offline(cpu)))

        self._update_treeview_style(cpu, conf.changed)

    def _get_active_cpu(self):
        """Helper function to get cpu from combobox"""
        # cpu_iter = self.cpu_box.get_active_iter()
        index = self.cpu_box.get_selected_index()
        if index != -1:
            return index
        # if cpu_iter is not None:
        #    return int(self.cpu_store[cpu_iter][0])

        # self.update_cpubox()
        return 0

    def _set_profile_settings(self, profile):
        """Set the settings based on the selected profile"""
        self.load_cpu_settings()  # Discard any changes

        # If no profile selected reset and disable apply_btn
        if profile.name == "No profile":
            self.toall.set_sensitive(True)
            for cpu, conf in self.settings.items():
                conf.reset_conf()
                self.update_tree_view(cpu, conf)
            return False

        self.toall.set_active(False)  # Turn off toggle
        self.toall.set_sensitive(False)  # Disable toggle
        prof_settings = profile.settings
        for cpu, settings in prof_settings.items():
            conf = self.settings.get(cpu)
            if not conf:
                continue
            conf.freqs_scaled = settings["freqs"]
            if settings["governor"] in conf.governors:
                conf.governor = settings["governor"]
            conf.online = settings["online"]
            self.update_tree_view(cpu, conf)
            self._update_treeview_style(cpu, conf.changed)
        return True

    def _set_sliders_sensitive(self, state):
        """Enable/Disable sliders and combo boxes"""
        self.spin_min.set_sensitive(state)
        self.spin_max.set_sensitive(state)
        self.min_sl.set_sensitive(state)
        self.max_sl.set_sensitive(state)
        self.gov_box.set_sensitive(state)
        self.energy_pref_box.set_sensitive(state)

    def _update_frequency_marks(self, cpu):
        """Add or remove slider marks for frequency steps

        Args:
            cpu: Index of cpu to query

        """
        # Clear marks
        self.min_sl.clear_marks()
        self.max_sl.clear_marks()

        if not self.tick_marks_enabled:
            return

        steps = self.get_cpu_frequency_steps(cpu)
        if not steps:
            minf = self.adj_min.get_lower()
            maxf = self.adj_min.get_upper()
            steps = [minf, maxf - (maxf - minf) / 2, maxf]

        markup = "{:1.2f}"
        for frequency in steps:
            freq = float(frequency / 1e3)
            mark = markup.format(freq)
            if self.ticks_markup:
                self.min_sl.add_mark(frequency, Gtk.PositionType.TOP, mark)
            else:
                self.min_sl.add_mark(frequency, Gtk.PositionType.TOP)
            self.max_sl.add_mark(frequency, Gtk.PositionType.TOP)

    def _update_energy_pref_box(self):
        """Updates the energy performance combobox"""
        cpu = self._get_active_cpu()
        conf = self.settings.get(cpu)

        energy_pref = conf.energy_pref_id
        energy_prefs = conf.energy_prefs

        if energy_pref != -1:
            pref_store = Gio.ListStore()
            for prefid, pref in enumerate(energy_prefs):
                if "_" in pref:
                    pref = pref.replace("_", " ")
                pref_store.append(EnergyPref(prefid, pref.capitalize()))

            self.energy_pref_box.bind_name_model(pref_store, lambda x: x.name)
            self.energy_pref_box.set_selected_index(energy_pref)
            self.energy_pref_box.set_sensitive(True)
        else:
            self.energy_pref_box.set_sensitive(False)

    def _update_gov_box(self):
        """Updates the governor combobox"""
        cpu = self._get_active_cpu()
        conf = self.settings.get(cpu)

        governor = conf.govid
        governors = conf.governors

        if governor is not None:
            gov_store = Gio.ListStore()
            for govid, gov in enumerate(governors):
                gov_store.append(Governor(govid, gov.capitalize()))

            self.gov_box.bind_name_model(gov_store, lambda x: x.name)
            self.gov_box.set_selected_index(governor)
            self.gov_box.set_sensitive(True)
        else:
            self.gov_box.set_sensitive(False)

    def _update_current_freq(self):
        """Callback to update the tree view with current CPU frequency"""
        for cpu in self.online_cpus:
            current_freq = read_current_freq(cpu) / 1e3
            self.tree_store[cpu][5] = current_freq
        return True

    def on_freq_edited(self, widget, path, value, index):
        """Update the sliders when frequencies change from table"""
        value = float(value)
        cpu = int(path)
        conf = self.settings[cpu]
        fmin, fmax = conf.freqs

        if cpu == self._get_active_cpu():
            if index == 2:
                self.adj_min.set_value(value)
            else:
                self.adj_max.set_value(value)
        else:
            if index == 2:
                conf.freqs = value, fmax
            else:
                conf.freqs = fmin, value

    def on_tree_toggled(self, widget, path):
        """Update online cpu toggle"""
        # check if it can be disabled
        allowed = bool(HELPER.cpu_allowed_offline(int(path)))
        if not allowed:
            return

        online = not self.tree_store[path][1]
        self.tree_store[path][1] = online
        self.settings[int(path)].online = online
        if int(path) == self._get_active_cpu():
            self.cpu_online.set_active(online)

    def _update_tree_view(self):
        """Updates the tree view"""
        self.tree_store = Gtk.ListStore(int, bool, float, float, str, float, int)
        for cpu, conf in self.settings.items():
            fmin, fmax = conf.freqs
            self.tree_store.append(
                [cpu, conf.online, fmin, fmax, conf.governor.capitalize(), 0.0, 0]
            )

        for i, column_title in enumerate(
            [
                _("CPU"),
                _("Online"),
                _("Min"),
                _("Max"),
                _("Governor"),
                _("Current freq."),
            ]
        ):
            if column_title == "Online":
                renderer = Gtk.CellRendererToggle()
                renderer.connect("toggled", self.on_tree_toggled)
                column = Gtk.TreeViewColumn(column_title, renderer, active=i)

            elif column_title == "Current freq.":
                renderer = Gtk.CellRendererSpin(digits=2)
                column = Gtk.TreeViewColumn(column_title, renderer, text=i, style=6)
                column.set_cell_data_func(renderer, self.conv_float, 5)

            elif column_title in ["Min", "Max"]:
                index = 2 if column_title == "Min" else 3
                adj = Gtk.Adjustment(
                    value=0,
                    lower=fmin,
                    upper=fmax,
                    step_increment=10,
                    page_increment=50,
                    page_size=0,
                )
                renderer = Gtk.CellRendererSpin(editable=True, adjustment=adj, digits=2)
                renderer.connect("edited", self.on_freq_edited, index)
                column = Gtk.TreeViewColumn(column_title, renderer, text=i, style=6)
                column.set_cell_data_func(renderer, self.conv_float, index)
            else:
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(column_title, renderer, text=i, style=6)
            self.tree_view.append_column(column)

        self.tree_view.set_model(self.tree_store)

    def update_tree_view(self, cpu, conf):
        """Update values inside the tree view"""
        if cpu == -1:
            for row in self.tree_store:
                row[2], row[3] = conf.freqs
                row[1] = conf.online
                row[4] = conf.governor.capitalize()
        else:
            row = self.tree_store[cpu]
            row[2], row[3] = conf.freqs
            row[1] = conf.online
            row[4] = conf.governor.capitalize()

    @Gtk.Template.Callback()
    def on_tree_selection(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            self.cpu_box.set_selected_index(model[treeiter][0])

    @Gtk.Template.Callback()
    def on_prefs_changed(self, pref, value):
        name = Gtk.Buildable.get_name(pref)
        value_str = str(value)
        if name == "default_profile_pref":
            mod = pref.get_model()
            ind = self.default_profile_pref.get_selected_index()
            self.conf.set("Profile", "profile", mod[ind].name)
        elif name == "default_allcpus":
            self.gui_conf["allcpus_default"] = value_str
        elif name == "default_ticks":
            self.tick_marks_enabled = value
            self.gui_conf["tick_marks_enabled"] = value_str
            self._update_frequency_marks(self._get_active_cpu())
        elif name == "default_ticks_num":
            self.ticks_markup = value
            self.gui_conf["frequency_ticks"] = value_str
            self._update_frequency_marks(self._get_active_cpu())
        elif name == "default_energy_per_cpu":
            self.gui_conf["energy_pref_per_cpu"] = value_str
            self.energy_per_cpu = value

        self.conf.write_settings()

    @Gtk.Template.Callback()
    def on_cpu_changed(self, widget, value):
        """Callback for cpu box"""
        # pylint: disable=W0612,W0613
        selection = self.tree_view.get_selection()
        index = widget.get_selected_index()
        if index > -1:
            selection.select_path(index)
        self.upd_sliders()

    @Gtk.Template.Callback()
    def on_toall_toggled(self, widget):
        """Enable/Disable cpu_box"""
        cpu = self._get_active_cpu()
        settings = self.settings[cpu]
        if widget.get_active():
            for cpu, conf in self.settings.items():
                conf.freqs = settings.freqs
                conf.governor = settings.governor
                conf.online = settings.online
                conf.energy_pref = settings.energy_pref
                self.update_tree_view(cpu, conf)
        self.apply_btn.set_sensitive(self.is_conf_changed)

    @Gtk.Template.Callback()
    def on_adj_min_value_changed(self, *args):
        """Callback for adj_min"""
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        cpu = self._get_active_cpu()
        fmin = self.adj_min.get_value()
        fmax = self.adj_max.get_value()
        fmin_hw, fmax_hw = self.settings[cpu].hw_lims

        if fmin > fmax:
            if fmin + 10 > fmax_hw:
                fmax = fmax_hw
            else:
                fmax = fmin + 10
        elif fmax < fmin:
            if fmax - 10 < fmin_hw:
                fmin = fmin_hw
            else:
                fmin = fmax - 10

        with self.lock():
            self.adj_min.set_value(fmin)
            self.adj_max.set_value(fmax)

        self._update_settings_freqs(cpu, fmin, fmax)
        self.apply_btn.set_sensitive(self.is_conf_changed)

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
            fmin = fmax - 10

        with self.lock():
            self.adj_min.set_value(fmin)

        self._update_settings_freqs(cpu, fmin, fmax)
        self.apply_btn.set_sensitive(self.is_conf_changed)

    @Gtk.Template.Callback()
    def on_refresh_clicked(self, *args):
        """Callback for refresh button"""
        if self.toall.get_active():
            for cpu in self.settings.keys():
                self._refresh_cpu_settings(cpu)
        else:
            cpu = self._get_active_cpu()
            self._refresh_cpu_settings(cpu)

    def _refresh_cpu_settings(self, cpu):
        self.settings[cpu].update_conf()
        self.update_tree_view(cpu, self.settings[cpu])

        if self.energy_pref_avail:
            if not self.energy_per_cpu:
                self._reset_energy_conf(-1)
            else:
                self._reset_energy_conf(cpu)
        self.upd_sliders()

    def on_cpu_online_toggled(self, *args):
        """Callback for cpu_online toggle"""
        if self.refreshing:
            return
        cpu = self._get_active_cpu()
        conf = self.settings[cpu]
        conf.online = self.cpu_online.get_active()
        self._set_sliders_sensitive(conf.online)
        self.apply_btn.set_sensitive(self.is_conf_changed)
        self.tree_store[cpu][1] = conf.online
        self._update_treeview_style(cpu, conf.changed)

    @Gtk.Template.Callback()
    def on_governor_changed(self, *args):
        """Callback for governor combobox
        Change governor and enable apply_btn
        """
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        mod = self.gov_box.get_model()
        gov = mod[self.gov_box.get_selected_index()]
        # Update store
        if self.toall.get_active():
            for cpu, row in enumerate(self.tree_store):
                conf = self.settings.get(cpu)
                conf.governor = gov.govid
                row[4] = gov.name
                self._update_treeview_style(cpu, conf.changed)
        else:
            cpu = self._get_active_cpu()
            conf = self.settings.get(cpu)
            conf.governor = gov.govid
            self.tree_store[cpu][4] = gov.name
            self._update_treeview_style(cpu, conf.changed)

        self.apply_btn.set_sensitive(self.is_conf_changed)

    @Gtk.Template.Callback()
    def on_energy_pref_box_changed(self, *args):
        """Callback for energy combobox
        Change energy pref and enable apply_btn
        """
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        mod = self.energy_pref_box.get_model()
        energy_pref = mod[self.energy_pref_box.get_selected_index()]
        active_cpu = self._get_active_cpu()

        # Note that tasks may by migrated from one CPU to another by the scheduler’s
        # load-balancing algorithm and if different energy vs performance hints are
        # set for those CPUs, that may lead to undesirable outcomes.
        # To avoid such issues it is better to set the same energy vs performance hint
        # for all CPUs or to pin every task potentially sensitive to them
        # to a specific CPU.
        # https://www.kernel.org/doc/html/v4.12/admin-guide/pm/intel_pstate.html#energy-vs-performance-hints

        error = False
        if self.energy_per_cpu:
            conf = self.settings.get(active_cpu)
            if conf.governor == "performance" and energy_pref.name != "Performance":
                error = True
                with self.lock():
                    self.energy_pref_box.set_selected_index(conf.energy_pref_id)
            else:
                conf.energy_pref = energy_pref.prefid
                self._update_treeview_style(active_cpu, conf.changed)

        else:
            for cpu, conf in self.settings.items():
                if conf.governor == "performance" and energy_pref.name != "Performance":
                    error = True
                    if cpu == active_cpu:
                        with self.lock():
                            self.energy_pref_box.set_selected_index(conf.energy_pref_id)
                    continue
                conf.energy_pref = energy_pref.prefid
                self._update_treeview_style(cpu, conf.changed)

        if error:
            error_message(
                "Energy profiles other than performance are not allowed when the governor is set to performance.",
                self,
            )
        self.apply_btn.set_sensitive(self.is_conf_changed)

    @Gtk.Template.Callback()
    def on_profile_changed(self, *args):
        """Callback for profile combobox
        Change profile and enable apply_btn
        """
        # pylint: disable=W0612,W0613
        if self.refreshing:
            return
        mod = self.profile_box.get_model()
        profile = mod[self.profile_box.get_selected_index()]
        # Update store
        self.profile = profile.name
        self._set_profile_settings(profile)
        self.upd_sliders()
        self.apply_btn.set_sensitive(self.is_conf_changed)

    @Gtk.Template.Callback()
    def on_apply_clicked(self, button):
        """Write changes back to sysfs"""
        ret = -1
        cpu = self._get_active_cpu()
        conf = self.settings[cpu]
        fmin, fmax = conf.freqs_scaled
        gov = conf.governor
        pref = conf.energy_pref

        if not HELPER.isauthorized():
            error_message("You don't have permissions to update cpu settings!", self)

        # Update only the cpus whose settings were changed
        changed_cpus = [cpu for cpu, conf in self.settings.items() if conf.changed]
        for cpu in changed_cpus:
            conf = self.settings.get(cpu)
            cpu_online = conf.online
            ret = self.set_cpu_online(cpu)
            if cpu_online:
                if conf.setting_changed("freqs"):
                    ret += self.set_cpu_frequencies(cpu)
                if conf.setting_changed("governor"):
                    ret += self.set_cpu_governor(cpu)
                if conf.setting_changed("energy_pref"):
                    ret += self.set_cpu_energy_preferences(cpu)

        for cpu in self.settings.keys():
            self._refresh_cpu_settings(cpu)

        # Update sliders
        self.profile_box.set_selected_index(0)

        self.load_cpu_settings()
        self.upd_sliders()

        if ret == 0:
            button.set_sensitive(False)
        else:
            error = ERRORS[ret]
            error_message(error, self)

    def on_prof_name_changed(self, entry, button):
        """Checks if there is text in entry"""
        if self.profile_name_entry.get_text() != "":
            button.set_sensitive(True)
        else:
            button.set_sensitive(False)

    def on_save_profile_clicked(self, button):
        """Callback saving the profile"""
        name = self.profile_name_entry.get_text().strip()
        self.conf.create_profile_from_settings(name, self.settings)
        self.profiles = self.conf.profiles
        self.update_profile_boxes()
        self.update_profiles_page()
        self.profile_name_entry.set_text("")

    def on_delete_profile_clicked(self, button, profile):
        """Callback for about"""
        message = Gtk.MessageDialog(
            transient_for=self,
            type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=_("Are you sure sure you want to delete this profile?"),
        )
        response = message.run()
        if response == Gtk.ResponseType.OK:
            self.conf.delete_profile(profile)
            self.profiles = self.conf.profiles
            self.update_profile_boxes()
            self.update_profiles_page()
        message.destroy()

    @Gtk.Template.Callback()
    def on_about_clicked(self, button):
        """Callback for about"""
        self.show_about_dialog()

    def show_about_dialog(self):
        """Shows the about dialog"""
        self.about_dialog.run()
        self.about_dialog.hide()

    @property
    def online_cpus(self):
        """Convenience function to get a list of available CPUs"""
        avail = HELPER.get_cpus_available()
        if avail:
            return [int(cpu) for cpu in avail]
        return avail

    @property
    def is_conf_changed(self):
        """Helper function to check if settings were changed"""
        changed = [cpu for cpu, conf in self.settings.items() if conf.changed]
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

    @staticmethod
    def conv_float(col, cell, model, treeiter, data):
        """Helper function to convert float to string with 2 decimal digits"""
        val = model.get(treeiter, data)[0]
        cell.set_property("text", "{:.2f}".format(val))

    def set_cpu_online(self, cpu):
        """Sets the online attribute for cpu

        Args:
            cpu: Index of cpu to set

        """
        conf = self.settings.get(cpu)
        if conf is None:
            return

        cpu_online = conf.online

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
        conf = self.settings.get(cpu)
        if conf is None:
            return ret

        gov = conf.governor
        # If govid is None means that there is an error with the kernel
        # https://github.com/vagnum08/cpupower-gui/issues/12
        if gov is None:
            return ret

        ret = HELPER.update_cpu_governor(cpu, gov)

        if ret != 0:
            return -11
        return ret

    def set_cpu_energy_preferences(self, cpu):
        """Sets the energy performance preference for cpu

        Args:
            cpu: Index of cpu to set

        """

        # Return success if not available
        if not self.energy_pref_avail:
            return 0

        ret = -1
        conf = self.settings.get(cpu)
        if conf is None:
            return ret

        pref = conf.energy_pref
        if not pref:
            return ret

        ret = HELPER.update_cpu_energy_prefs(cpu, pref)

        if ret != 0:
            return -12
        return ret

    def set_cpu_frequencies(self, cpu):
        """Sets the frequency limits for cpu

        Args:
            cpu: Index of cpu to set

        """
        ret = -1
        conf = self.settings.get(cpu)
        if conf is None:
            return ret

        fmin, fmax = conf.freqs_scaled
        if (fmin is not None) and (fmax is not None):
            ret = HELPER.update_cpu_settings(cpu, fmin, fmax)
        if ret != 0:
            return -13
        return ret
