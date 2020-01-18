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

from gi.repository import Gtk, Gio, GLib

try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3 as AppIndicator
except:
    AppIndicator = None

from .window import CpupowerGuiWindow

BUS = dbus.SystemBus()
SESSION = BUS.get_object(
    "org.rnd2.cpupower_gui.helper", "/org/rnd2/cpupower_gui/helper"
)

HELPER = dbus.Interface(SESSION, "org.rnd2.cpupower_gui.helper")
APP_ID = "org.rnd2.cpupower_gui"


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )

        self.add_main_option(
            "performance",
            ord("p"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Change governor to performance",
            None,
        )
        self.add_main_option(
            "balanced",
            ord("b"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Change governor to balanced",
            None,
        )

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
            builder = Gtk.Builder()
            builder.add_from_resource("/org/rnd2/cpupower_gui/tray.ui")
            builder.get_object("sw_perf").connect("activate", self.on_apply_performance)
            builder.get_object("sw_balance").connect("activate", self.on_apply_default)
            builder.get_object("quit").connect("activate", self.do_quit)
            self.indicator.set_menu(builder.get_object("tray_menu"))

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = CpupowerGuiWindow(application=self)
        win.present()

    def do_quit(self, *args):
        exit(0)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        # convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        if "performance" in options:
            print("Setting governor to performance")
            self.activate_action("Performance")
            return 0

        if "balanced" in options:
            print("Setting governor to default")
            self.activate_action("Balanced")
            return 0

        self.activate()
        return 0

    def on_apply_performance(self, params=None, platform_data={}):
        ret = -1
        for cpu in HELPER.get_cpus_available():
            gov = "performance"
            if dbus.String(gov) not in HELPER.get_cpu_governors(cpu):
                perf_gov = "schedutil"
                if dbus.String(gov) not in HELPER.get_cpu_governors(cpu):
                    print("Failed to set governor to performance")
                    return ret

            if HELPER.isauthorized():
                ret = HELPER.update_cpu_governor(cpu, gov)
                if ret == 0:
                    print("Set CPU {} to {}".format(int(cpu), gov))

        # Update window if exists
        win = self.props.active_window
        if win:
            win.upd_sliders()

        return ret

    def on_apply_default(self, params=None, platform_data={}):
        ret = -1
        for cpu in HELPER.get_cpus_available():
            govs = HELPER.get_cpu_governors(cpu)
            for governor in govs:
                if str(governor) != "performance":
                    break

            gov = str(governor)
            if not gov:
                print("Failed to get default governor for CPU {}.".format(int(cpu)))
                continue

            if HELPER.isauthorized():
                ret = HELPER.update_cpu_governor(cpu, gov)
                if ret == 0:
                    print("Set CPU {} to {}".format(int(cpu), gov))

        # Update window if exists
        win = self.props.active_window
        if win:
            win.upd_sliders()

        return ret


def main(version):
    app = Application()
    return app.run(sys.argv)
