#!/usr/bin/env python3
# __main__.py

"""
Copyright (C) 2017 [RnD]²

This file is part of cpupower-gui.

cpupower-gui is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

cpupower-gui is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with cpupower-gui.  If not, see <http://www.gnu.org/licenses/>.

Author: Evangelos Rigas <erigas@rnd2.org>
"""

import os, sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

syspath = "/sys/devices/system/cpu/cpu0/cpufreq"
freq_min_var = "scaling_min_freq"
freq_max_var = "scaling_max_freq"
freq_minhw_var = "cpuinfo_min_freq"
freq_maxhw_var = "cpuinfo_max_freq"
avail_gov_var = "scaling_available_governors"
governor_var = "scaling_governor"
online = '/sys/devices/system/cpu/online'


def read_settings(cpu):
    spath = syspath.format(cpu)
    with open(os.path.join(spath, freq_min_var), "r") as f:
        freq_min = int(f.readline())

    with open(os.path.join(spath, freq_max_var), "r") as f:
        freq_max = int(f.readline())

    with open(os.path.join(spath, freq_minhw_var), "r") as f:
        freq_minhw = int(f.readline())

    with open(os.path.join(spath, freq_maxhw_var), "r") as f:
        freq_maxhw = int(f.readline())

    with open(os.path.join(spath, avail_gov_var), "r") as f:
        govs = f.readline().strip().split(" ")
        governors = {}
        for n, item in enumerate(govs):
            governors[n] = item

    with open(os.path.join(spath, governor_var), "r") as f:
        governor = f.readline().strip()
    return freq_min, freq_minhw, freq_max, freq_maxhw, governors, governor


class Application(Gtk.Application):
    global online

    def __init__(self, **kwargs):
        super().__init__(application_id='org.gnome.CpupowerGui',
                         **kwargs)
        with open(online, "r") as f:
            r = f.readline().strip().split('-')[-1]
            self.cpu_avail = int(r) + 1
        self.widgets = {}

    def do_activate(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("/usr/share/cpupower-gui/ui/cpupower.glade")

        cpu_store = Gtk.ListStore(int, int)
        for i in range(self.cpu_avail):
            cpu_store.append([i, i])

        self['cpubox'].set_model(cpu_store)
        self['cpubox'].set_active(0)

        self.upd_sliders()

        self.builder.connect_signals(self)

        window = self.builder.get_object("window")
        window.show_all()
        Gtk.main()

    def upd_sliders(self):
        cpu = self['cpubox'].get_active()
        freq_min, self.freq_minhw, freq_max, self.freq_maxhw, self.governors, self.governor = read_settings(cpu)

        gov_store = Gtk.ListStore(str, int)
        for gov in self.governors.items():
            if gov[1] == self.governor:
                gov_id = gov[0]
            gov_store.append([gov[1].capitalize(), gov[0]])

        self['govbox'].set_model(gov_store)
        self['govbox'].set_active(gov_id)
        self['govbox'].set_active(gov_id)

        self['adj_min'].set_lower(int(self.freq_minhw / 1000))
        self['adj_min'].set_upper(int(self.freq_maxhw / 1000))
        self['adj_max'].set_lower(int(self.freq_minhw / 1000))
        self['adj_max'].set_upper(int(self.freq_maxhw / 1000))
        self['adj_min'].set_value(int(freq_min / 1000))
        self['adj_max'].set_value(int(freq_max / 1000))
        self['applybtn'].set_sensitive(False)

    def on_cancel_clicked(self, *args):
        Gtk.main_quit(*args)

    def on_window_destroy(self, *args):
        Gtk.main_quit(*args)

    def on_cpu_changed(self, *args):
        self.upd_sliders()

    def on_toall_state_set(self, switch, val):
        if val:
            self['cpubox'].set_sensitive(False)
        else:
            self['cpubox'].set_sensitive(True)

    def on_adj_min_value_changed(self, *args):
        if self['adj_min'].get_value() > self['adj_max'].get_value():
            if self['adj_min'].get_value() + 10 > self.freq_maxhw / 1000:
                self['adj_max'].set_value(self.freq_maxhw / 1000)
            else:
                self['adj_max'].set_value(self['adj_min'].get_value() + 10)
        elif self['adj_max'].get_value() < self['adj_min'].get_value():
            if self['adj_max'].get_value() - 10 < self.freq_minhw / 1000:
                self['adj_min'].set_value(self.freq_minhw / 1000)
            else:
                self['adj_min'].set_value(self['adj_max'].get_value() - 10)
        self['applybtn'].set_sensitive(True)

    def on_adj_max_value_changed(self, *args):
        if self['adj_max'].get_value() < self['adj_min'].get_value():
            self['adj_min'].set_value(self['adj_max'].get_value() - 10)
        self['applybtn'].set_sensitive(True)

    def on_governor_changed(self, *args):
        mod = self['govbox'].get_model()
        text, tid = mod[self['govbox'].get_active_iter()][:2]
        self.governor = self.governors[tid]
        self['applybtn'].set_sensitive(True)

    def on_apply_clicked(self, button):
        fmin = int(self['adj_min'].get_value() * 1000)
        fmax = int(self['adj_max'].get_value() * 1000)
        try:
            if self['toall'].get_active():
                for i in range(self.cpu_avail):
                    spath = syspath.format(i)

                    with open(os.path.join(spath, freq_min_var), "w") as f:
                        f.write(str(fmin))
                    with open(os.path.join(spath, freq_max_var), "w") as f:
                        f.write(str(fmax))
                    with open(os.path.join(spath, governor_var), "w") as f:
                        f.write(self.governor)
            else:
                spath = syspath.format(self['cpubox'].get_active())

                with open(os.path.join(spath, freq_min_var), "w") as f:
                    f.write(str(fmin))
                with open(os.path.join(spath, freq_max_var), "w") as f:
                    f.write(str(fmax))
                with open(os.path.join(spath, governor_var), "w") as f:
                    f.write(self.governor)
            button.set_sensitive(False)
        except PermissionError as e:
            message = Gtk.MessageDialog(type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK)
            message.set_markup(str(e))
            message.show()
            message.connect("response", self.dialog_response)

    def dialog_response(self, widget, response_id):
        # if the button clicked gives response OK (-5)
        if response_id == Gtk.ResponseType.OK:
            print("OK")
        # if the messagedialog is destroyed (by pressing ESC)
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            print("dialog closed or cancelled")
        # finally, destroy the messagedialog
        widget.destroy()

    def __getitem__(self, name):
        """ Convince method that allows widgets to be accessed via self["widget"] """
        if name in self.widgets:
            return self.widgets[name]
        return self.builder.get_object(name)

    def __setitem__(self, name, item):
        """ Convince method that allows widgets to be accessed via self["widget"] """
        self.widgets[name] = item

    def __contains__(self, name):
        """ Returns True if there is such widget """
        if name in self.widgets: return True
        return self.builder.get_object(name) != None


def main():
    application = Application()

    try:
        ret = application.run()#sys.argv)
    except SystemExit as e:
        ret = e.code
    sys.exit(ret)


if __name__ == '__main__':
    main()


