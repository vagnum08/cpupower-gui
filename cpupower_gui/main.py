# main.py
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
import gi

# Gtk.Template requires at least version 3.30
gi.check_version("3.30")

gi.require_version("Gtk", "3.0")

from gi.repository import Gio, GLib, Gtk

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):
    AppIndicator = None

from .helper import apply_balanced, apply_performance, apply_cpu_profile
from .window import CpupowerGuiWindow
from .config import CpuPowerConfig

BUS = dbus.SystemBus()
SESSION = BUS.get_object(
    "org.rnd2.cpupower_gui.helper", "/org/rnd2/cpupower_gui/helper"
)

HELPER = dbus.Interface(SESSION, "org.rnd2.cpupower_gui.helper")
APP_ID = "org.rnd2.cpupower_gui"


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

        action = Gio.SimpleAction.new("Performance", None)
        action.connect("activate", self.on_apply_performance)
        self.add_action(action)

        action = Gio.SimpleAction.new("Balanced", None)
        action.connect("activate", self.on_apply_default)
        self.add_action(action)

        if AppIndicator:
            self.indicator = AppIndicator.Indicator.new(
                APP_ID, APP_ID, AppIndicator.IndicatorCategory.APPLICATION_STATUS
            )
            self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
            self.indicator.set_menu(self.create_menu())

    def create_menu(self):
        menu = Gtk.Menu()
        config = CpuPowerConfig()
        profiles = [config.get_profile(profile) for profile in config.profiles]
        # Built-in profiles
        for profile in profiles:
            if profile._custom:
                continue
            item = Gtk.MenuItem(profile.name)
            item.connect("activate", self.on_apply_profile, profile)
            menu.append(item)

        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)

        # System profiles
        for profile in profiles:
            if profile.system:
                item = Gtk.MenuItem(profile.name)
                item.connect("activate", self.on_apply_profile, profile)
                menu.append(item)

        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)

        # User profiles
        for profile in profiles:
            if profile._custom and not profile.system:
                item = Gtk.MenuItem(profile.name)
                item.connect("activate", self.on_apply_profile, profile)
                menu.append(item)

        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)

        exittray = Gtk.MenuItem("Quit")
        exittray.connect("activate", self.do_quit)
        menu.append(exittray)

        menu.show_all()
        return menu

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = CpupowerGuiWindow(application=self)
        win.present()

    def do_quit(self, *args):
        exit(0)

    def on_apply_profile(self, params=None, profile=None):
        apply_cpu_profile(profile)

        # Update window if exists
        win = self.props.active_window
        if win:
            for cpu in win.settings.keys():
                win._refresh_cpu_settings(cpu)

        return 0

    def on_apply_performance(self, params=None, platform_data={}):
        apply_performance()

        # Update window if exists
        win = self.props.active_window
        if win:
            for cpu in win.settings.keys():
                win._refresh_cpu_settings(cpu)

        return 0

    def on_apply_default(self, params=None, platform_data={}):
        apply_balanced()

        # Update window if exists
        win = self.props.active_window
        if win:
            for cpu in win.settings.keys():
                win._refresh_cpu_settings(cpu)

        return 0


def main(version):
    app = Application()
    return app.run(sys.argv)
