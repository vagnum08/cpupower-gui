"""Module for dbus helper"""

import dbus

from .utils import cpus_available, read_available_energy_prefs, read_govs

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
    if not HELPER.isauthorized():
        print("User is not authorised. No changes applied.")
        return -1

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
        print(MSG.format(cpu, fmin / 1e3, fmax / 1e3, gov.capitalize(), online))


def apply_configuration(config):
    """Set cpu settings base on configuration

    Args:
        config: A cpupower configuration object

    """
    # TODO: Allow extra configuration to take place
    profile = config.default_profile
    if profile not in config.profiles:
        return -1

    apply_cpu_profile(config.get_profile(profile))


def apply_performance():
    """Set CPU governor to performance"""
    if not HELPER.isauthorized():
        print("User is not authorised. No changes applied.")
        return -1

    for cpu in cpus_available():
        gov = "performance"
        if gov not in read_govs(cpu):
            gov = "schedutil"
            if gov not in read_govs(cpu):
                print("Failed to set governor to performance")

        ret = HELPER.update_cpu_governor(cpu, gov)
        if ret == 0:
            print("Set CPU {} to {}".format(cpu, gov))

    return 0


def apply_balanced():
    """Set CPU governor to powersave or ondemand"""
    if not HELPER.isauthorized():
        print("User is not authorised. No changes applied.")
        return -1

    for cpu in cpus_available():
        govs = read_govs(cpu)
        for governor in govs:
            if governor != "performance":
                break

        gov = governor
        if not gov:
            print("Failed to get default governor for CPU {}.".format(cpu))
            continue

        ret = HELPER.update_cpu_governor(cpu, gov)
        if ret == 0:
            print("Set CPU {} to {}".format(cpu, gov))

    return 0


def apply_energy_preference(pref):
    """Set CPU energy profile"""
    if not HELPER.isauthorized():
        print("User is not authorised. No changes applied.")
        return -1

    for cpu in cpus_available():
        if pref not in read_available_energy_prefs(cpu):
            print("Preference not available for CPU {}.".format(cpu))
            continue

        ret = HELPER.update_cpu_energy_prefs(cpu, pref)
        if ret == 0:
            print("Set CPU {} to {}".format(cpu, pref))

    return 0
