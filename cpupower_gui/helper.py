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
        print(MSG.format(cpu, fmin / 1e3, fmax / 1e3, gov.capitalize(), online))


def apply_configuration(config):
    """Set cpu settings base on configuration

    Args:
        config: A cpupower configuration object

    """
    # TODO: Allow extra configuration to take place
    profile = config.default_profile
    if not profile in config.profiles:
        return

    apply_cpu_profile(config.get_profile(profile))

def apply_performance():
    """Set CPU governor to performance"""
    for cpu in HELPER.get_cpus_available():
        gov = "performance"
        if dbus.String(gov) not in HELPER.get_cpu_governors(cpu):
            gov = "schedutil"
            if dbus.String(gov) not in HELPER.get_cpu_governors(cpu):
                print("Failed to set governor to performance")

        if HELPER.isauthorized():
            ret = HELPER.update_cpu_governor(cpu, gov)
            if ret == 0:
                print("Set CPU {} to {}".format(int(cpu), gov))

def apply_balanced():
    """Set CPU governor to powersave or ondemand"""
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
