"""Module for dbus helper"""

import dbus

BUS = dbus.SystemBus()
SESSION = BUS.get_object(
    "org.rnd2.cpupower_gui.helper", "/org/rnd2/cpupower_gui/helper"
)

HELPER = dbus.Interface(SESSION, "org.rnd2.cpupower_gui.helper")

MSG = """Setting CPU: {}
    Minimum Frequency: {} MHz, Maximum Frequency: {} MHz
    Governor: {}, Online: {}
"""


def apply_cpu_profile(profile):
    """Set cpu settings base on a profile

    Args:
        profile: A cpupower profile

    """
    settings = profile.settings
    for cpu in settings.keys():
        fmin, fmax = settings[cpu].get("freqs")
        gov = settings[cpu].get("governor")
        online = settings[cpu].get("online")
        if fmin and fmax:
            HELPER.update_cpu_settings(cpu, fmin, fmax)
        if gov:
            HELPER.update_cpu_governor(cpu, gov)
        if online is not None:
            if HELPER.cpu_allowed_offline(cpu):
                if online:
                    HELPER.set_cpu_online(cpu)
                else:
                    HELPER.set_cpu_offline(cpu)
        print(MSG.format(cpu, fmin/1e3, fmax/1e3, gov.capitalize(), online))
