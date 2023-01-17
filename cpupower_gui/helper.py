"""Module for dbus helper"""

import dbus

from .utils import (
    cpus_available,
    read_available_energy_prefs,
    read_govs,
    is_online,
    read_governor,
    read_freq_lims,
    read_freqs,
)

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
        online = settings[cpu].get("online")
        fmin = 0
        fmax = 0
        gov = settings[cpu].get("governor")

        if online is not None:
            if HELPER.cpu_allowed_offline(cpu):
                if online:
                    HELPER.set_cpu_online(cpu)
                else:
                    HELPER.set_cpu_offline(cpu)

        if online:
            fmin, fmax = settings[cpu].get("freqs")
            if fmin and fmax:
                HELPER.update_cpu_settings(cpu, fmin, fmax)

            if gov:
                HELPER.update_cpu_governor(cpu, gov)

        gov = read_governor(cpu)  # Refetch this to workaround bug
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
    """Set CPU governor to schedutil/ondemand/powersave"""
    if not HELPER.isauthorized():
        print("User is not authorised. No changes applied.")
        return -1

    for cpu in cpus_available():
        govs = read_govs(cpu)

        if "schedutil" in govs:
            gov = "schedutil"
        elif "ondemand" in govs:
            gov = "ondemand"
        elif "powersave" in govs:
            gov = "powersave"
        else:
            for governor in govs:
                if governor != "performance":
                    gov = governor
                    break

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


def set_cpu_offline(cpu):
    """Set cpu to offline"""
    if not HELPER.isauthorized():
        print("User is not authorised. No changes applied.")
        return -1

    try:
        ret = HELPER.set_cpu_offline(cpu)
    except dbus.exceptions.DBusException:
        ret = -1

    if ret == 0:
        print("OK")
    else:
        print("Failed!")


def set_cpu_online(cpu):
    """Set cpu to online"""
    if not HELPER.isauthorized():
        print("User is not authorised. No changes applied.")
        return -1

    ret = HELPER.set_cpu_online(cpu)
    if ret == 0:
        print("OK")
    else:
        print("Failed!")


def set_cpu_min_freq(cpu, freq):
    """Set minimum frequency for CPU

    Args:
        cpu: The core number to change
        freq: The frequency in MHz

    """
    freq = int(freq * 1e3)
    if cpu in cpus_available():
        fmin, fmax = read_freqs(cpu)
        hmin, hmax = read_freq_lims(cpu)
        if hmin <= freq <= hmax:
            HELPER.update_cpu_settings(cpu, freq, fmax)
            print("OK")
        else:
            print("Frequency out of range: {} < freq < {}".format(hmin, hmax))


def set_cpu_max_freq(cpu, freq):
    """Set maximum frequency for CPU

    Args:
        cpu: The core number to change
        freq: The frequency in MHz

    """
    freq = int(freq * 1e3)
    if cpu in cpus_available():
        fmin, fmax = read_freqs(cpu)
        hmin, hmax = read_freq_lims(cpu)
        if hmin <= freq <= hmax:
            HELPER.update_cpu_settings(cpu, fmin, freq)
            print("OK")
        else:
            print(
                "Frequency out of range: {} < freq < {}".format(hmin / 1e3, hmax / 1e3)
            )


def get_cpu_frequencies(cpu):
    """Return frequencies for cpu"""
    fmin, fmax = read_freqs(cpu)
    hmin, hmax = read_freq_lims(cpu)
    return (fmin / 1e3, fmax / 1e3), (hmin / 1e3, hmax / 1e3)
