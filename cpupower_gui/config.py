"""Class for reading configuration files"""

from configparser import ConfigParser
from pathlib import Path
from shlex import split

from xdg import BaseDirectory

from cpupower_gui.utils import (
    read_govs,
    read_governor,
    read_freq_lims,
    read_freqs,
    cpus_available,
    is_online,
    parse_core_list,
)


XDG_PATH = Path(BaseDirectory.save_config_path("cpupower_gui"))


class CpuPowerConfig:
    """cpupower configuration class"""

    etc_conf = Path("/etc/cpupower_gui.conf")
    etc_confd = Path("/etc/cpupower_gui.d")
    user_conf = XDG_PATH

    def __init__(self):
        self.config = ConfigParser()
        self.config.add_section("Profile")
        self.config.add_section("GUI")
        self.config.set("Profile", "profile", "Balanced")
        self._profiles = {}
        # Initialise class
        self._generate_default_profiles()
        self._read_configuration()
        self._read_profiles()

    def _read_configuration(self):
        """Read and parse configuration files from
        /etc/cpupower_gui.d/ and XDG_CONFIG_HOME

        """
        if self.etc_conf.exists():
            self.config.read(self.etc_conf)

        # drop-in configuration
        if self.etc_confd.exists():
            confd_files = sorted(self.etc_confd.glob("*.conf"))
            if confd_files:
                self.config.read(confd_files)

        # user configuration
        conf_files = sorted(self.user_conf.glob("*.conf"))
        if conf_files:
            self.config.read(conf_files)

    def _read_profiles(self):
        """Read .profile files from configuration directories"""
        files = self.user_conf.glob("*.profile")
        for file in files:
            prof = Profile(file)
            self._profiles.update({prof.name: prof})

    @property
    def default_profile(self):
        """Returns selected profile

        Returns:
            default_profile: Default profile name
        """
        return self.config["Profile"].get("profile")

    @property
    def profiles(self):
        """Return list with profiles"""
        return list(self._profiles.keys())

    def get_profile(self, name):
        """Return named profile object
        Args:
            name: Name of the profile

        Returns:
            profile: Profile object

        """
        return self._profiles.get(name)

    def get_profile_settings(self, name):
        """Returns profile settings

        Args:
            name: Name of the profile

        Returns:
            settings: Profile settings

        """
        if name in self._profiles:
            return self._profiles[name].settings
        return None

    def get_gui_settings(self):
        """Returns GUI settings

        Returns:
            settings: GUI settings

        """
        return self.config["GUI"]

    def _generate_default_profiles(self):
        """Generate default profiles based on current hardware.
        The two profiles generated are 'Balanced' and 'Performance'.
        The profiles apply either powersaving or performance governor.

        """
        # Get a governor list from first cpu
        govs = read_govs(0)
        if not govs:
            return

        # generate balanced profile based on powersave/ondemand governor
        if "powersave" in govs:
            self._profiles["Balanced"] = DefaultProfile("Balanced", "powersave")
        elif "ondemand" in govs:
            self._profiles["Balanced"] = DefaultProfile("Balanced", "ondemand")

        # generate performance profile based on performance governor
        if "performance" in govs:
            self._profiles["Performance"] = DefaultProfile("Performance", "performance")


class Profile:
    """Wrapper for .profile files"""

    def __init__(self, filename=None):
        self.settings = {}
        self.name = ""
        self.file = None
        if filename:
            self.file = Path(filename)
            self.parse_file()

    def parse_file(self):
        """Parse .profile file"""
        if not self.file.exists():
            return

        text = self.file.read_text().splitlines()
        # read name
        if "name:" in text[0]:
            self.name = split(text[0])[-1]
        else:
            self.name = self.file.name

        for line in text[1:]:
            vals = split(line, comments=True)
            if vals:
                self.settings.update(self._read_values(*vals))

    @staticmethod
    def _read_values(cpus: str, fmin: str, fmax: str, governor: str, online="y"):
        """Return settings dict from parsed settings

        Args:
            cpus: String with related cores
            fmin: Minimum core frequency
            fmax: Maximum core frequency
            governor: Core governor
            online: If core is online or offline

        Returns:
            settings (dict): Dictionary with parsed settings

        """
        settings = {}
        # cpu, fmin, fmax, gov
        cores = parse_core_list(cpus)
        for core in cores:
            # Skip core if not available
            if core not in cpus_available():
                continue

            conf = {
                "freqs": parse_freqs(core, fmin, fmax),
                "governor": parse_governor(core, governor),
                "online": parse_online(core, online),
            }
            settings.update({core: conf})
        return settings


class DefaultProfile(Profile):
    """Class for the default profiles"""

    def __init__(self, name: str, governor="-", fmin="-", fmax="-"):
        super().__init__()
        self.name = name
        self._generate_profile(fmin, fmax, governor)

    def _generate_profile(self, fmin: str, fmax: str, governor: str):
        """Generate default settings

        Args:
            fmin: Minimum core frequency
            fmax: Maximum core frequency
            governor: Core governor

        """
        for core in cpus_available():
            conf = self._read_values(str(core), fmin, fmax, governor)
            self.settings.update(conf)


#
# Helper function for parsing profiles
#


def parse_freqs(cpu: int, fmin: str, fmax: str):
    """Return valid fmin, fmax for cpu from config

    Args:
        cpu: The cpu to check as an integer
        fmin: The minimum frequency
        fmax: The maximum frequency

    Returns:
        fmin, fmax: A tuple with the frequencies

    """
    freq_min, freq_max = None, None
    if cpu not in cpus_available():
        return freq_min, freq_max

    if fmin.isnumeric():
        freq_min = int(fmin) * 1000
    else:
        fmin, _ = read_freq_lims(cpu)
        freq_min = fmin

    if fmax.isnumeric():
        freq_max = int(fmax) * 1000
    else:
        _, fmax = read_freq_lims(cpu)
        freq_max = fmax

    return freq_min, freq_max


def parse_governor(cpu: int, gov: str):
    """Return valid governor for cpu from config

    Args:
        cpu: The cpu to check as an integer
        gov: The governor value from config

    Returns:
        governor: A valid governor

    """
    if cpu not in cpus_available():
        return None

    governors = read_govs(cpu)
    if not governors:
        return None

    if gov in governors:
        return gov

    return governors[0]


def parse_online(cpu: int, online: str):
    """Return valid online attribute for cpu from config

    Args:
        cpu: The cpu to check as an integer
        online: The online value from config

    Returns:
        online: A valid online attribute value

    """
    if cpu not in cpus_available():
        return None

    if online.lower() in ["yes", "y", "1", "true"]:
        return True

    return False


class CpuSettings:
    """Abstraction class for cpu settings"""

    def __init__(self, cpu):
        self.cpu = cpu
        self._settings = {}
        self._new_settings = {}
        # Attributes that don't change
        self._lims = read_freq_lims(cpu)
        self._governors = read_govs(cpu)
        self.update_conf()

    def update_conf(self):
        cpu = self.cpu
        self._settings["freqs"] = read_freqs(cpu)
        self._settings["governor"] = read_governor(cpu)
        self._settings["online"] = is_online(cpu)
        # In case a new governor has been added
        self._governors = read_govs(cpu)
        self.reset_conf()

    def reset_conf(self):
        # Reset changed values
        self._new_settings = self._settings.copy()

    def __repr__(self):
        return "Cpu: {}\nFreqs: {}\nGovernor: {}\n".format(
            self.cpu, self.freqs, self.governor
        )

    @property
    def changed(self):
        return self._settings != self._new_settings

    @property
    def freqs(self):
        freqs = self._new_settings["freqs"]
        return int(freqs[0] / 1e3), int(freqs[1] / 1e3)

    @freqs.setter
    def freqs(self, freqs):
        self._new_settings["freqs"] = (int(freqs[0] * 1e3), int(freqs[1] * 1e3))

    @property
    def freqs_scaled(self):
        freqs = self._new_settings["freqs"]
        return freqs[0], freqs[1]

    @freqs_scaled.setter
    def freqs_scaled(self, freqs):
        self._new_settings["freqs"] = (freqs[0], freqs[1])

    @property
    def governor(self):
        return self._new_settings["governor"]

    @governor.setter
    def governor(self, gov):
        conf = self._new_settings
        if isinstance(gov, str):
            conf["governor"] = gov

        if isinstance(gov, int):
            conf["governor"] = self._governors[gov]

    @property
    def governors(self):
        return self._governors

    @property
    def govid(self):
        return self._governors.index(self.governor)

    @property
    def hw_lims(self):
        freqs = self._lims
        return int(freqs[0] / 1e3), int(freqs[1] / 1e3)

    @property
    def online(self):
        return self._new_settings.get("online")

    @online.setter
    def online(self, on):
        self._new_settings["online"] = bool(on)
