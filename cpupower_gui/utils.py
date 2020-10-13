from pathlib import Path

SYS_PATH = "/sys/devices/system/cpu/cpu{}/cpufreq"
FREQ_MIN = "scaling_min_freq"
FREQ_MAX = "scaling_max_freq"
FREQ_MIN_HW = "cpuinfo_min_freq"
FREQ_MAX_HW = "cpuinfo_max_freq"
AVAIL_FREQS = "scaling_available_frequencies"
AVAIL_GOV = "scaling_available_governors"
AVAIL_PERF_PREF = "energy_performance_available_preferences"
PERF_PREF = "energy_performance_preference"
GOVERNOR = "scaling_governor"
ONLINE = Path("/sys/devices/system/cpu/online")
PRESENT = Path("/sys/devices/system/cpu/present")
ONLINE_PATH = "/sys/devices/system/cpu/cpu{}/online"


def parse_core_list(string):
    """Parse string of cores like '0,2,4-10,12' into a list """
    cores = []
    for elem in string.split(","):
        if "-" in elem:
            start, end = [int(c) for c in elem.split("-")]
            cores.extend(range(start, end + 1))
        else:
            cores.append(int(elem))
    return cores


def cpus_present():
    """Returns a list of present CPUs """
    cpus = PRESENT.read_text().strip()
    return parse_core_list(cpus)


def cpus_online():
    """Returns a list of online CPUs """
    cpus = ONLINE.read_text().strip()
    return parse_core_list(cpus)


def cpus_offline():
    """Returns a list of offline CPUs """
    online = cpus_online()
    present = cpus_present()
    return [cpu for cpu in present if cpu not in online]


def cpus_available():
    online = cpus_present()
    avail = []
    for cpu in online:
        sys_path = Path(SYS_PATH.format(cpu))
        if (
            (sys_path / FREQ_MIN_HW).exists()
            and (sys_path / FREQ_MAX_HW).exists()
            and (sys_path / AVAIL_GOV).exists()
        ):
            avail.append(cpu)
    return avail


def is_online(cpu):
    """Wrapper to get the online state for a cpu

    Args:
        cpu: Index of cpu to query

    Returns:
        bool: True if cpu is online, False otherwise

    """

    online = cpus_online()
    present = cpus_present()
    return (cpu in present) and (cpu in online)


def read_freqs(cpu):
    """ Reads frequencies from sysfs """
    sys_path = Path(SYS_PATH.format(int(cpu)))

    freq_min = int((sys_path / FREQ_MIN).read_text())
    freq_max = int((sys_path / FREQ_MAX).read_text())

    return freq_min, freq_max


def read_freq_lims(cpu):
    """ Reads frequency limits from sysfs """
    try:
        sys_path = Path(SYS_PATH.format(int(cpu)))
        freq_minhw = int((sys_path / FREQ_MIN_HW).read_text())
        freq_maxhw = int((sys_path / FREQ_MAX_HW).read_text())

        return freq_minhw, freq_maxhw
    except Exception as exc:
        print("WARNING! Unknown CPU frequency, cause:", exc)

    return 0, 0


def read_govs(cpu):
    """ Reads governors from sysfs """
    sys_path = Path(SYS_PATH.format(int(cpu)))
    try:
        sys_file = sys_path / AVAIL_GOV
        govs = sys_file.read_text().strip().split(" ")
    except OSError:
        govs = []
    finally:
        return govs


def read_available_frequencies(cpu):
    """ Reads available frequencies from sysfs """
    sys_path = Path(SYS_PATH.format(int(cpu)))
    try:
        sys_file = sys_path / AVAIL_FREQS
        freqs = sys_file.read_text().strip().split(" ")
    except OSError:
        freqs = []
    finally:
        return freqs


def read_governor(cpu):
    """ Reads governor from sysfs """
    sys_path = Path(SYS_PATH.format(int(cpu)))
    try:
        sys_file = sys_path / GOVERNOR
        governor = sys_file.read_text().strip()
    except OSError:
        governor = "ERROR"
    finally:
        return governor


def read_available_energy_prefs(cpu):
    """ Reads energy performance available preferences"""
    sys_path = Path(SYS_PATH.format(int(cpu)))
    try:
        sys_file = sys_path / AVAIL_PERF_PREF
        prefs = sys_file.read_text().strip().split(" ")
    except OSError:
        prefs = []
    finally:
        return prefs


def read_energy_pref(cpu):
    """ Reads energy performance available preferences"""
    sys_path = Path(SYS_PATH.format(int(cpu)))
    try:
        sys_file = sys_path / PERF_PREF
        pref = sys_file.read_text().strip()
    except OSError:
        pref = ""
    finally:
        return pref


def is_energy_pref_avail(cpu):
    """Check if Intel energy performance preferences are available"""
    sys_path = Path(SYS_PATH.format(int(cpu)))
    sys_file = sys_path / AVAIL_PERF_PREF
    return sys_file.exists()
