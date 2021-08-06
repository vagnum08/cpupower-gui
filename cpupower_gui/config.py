"""Class for reading configuration files"""

from configparser import ConfigParser
from pathlib import Path
from shlex import split

try:
    from xdg import BaseDirectory

    XDG_PATH = Path(BaseDirectory.save_config_path("cpupower_gui"))
except ImportError:
    BaseDirectory = None
    XDG_PATH = None

from cpupower_gui.utils import (
    cpus_available,
    is_energy_pref_avail,
    is_online,
    parse_core_list,
    read_available_energy_prefs,
    read_energy_pref,
    read_freq_lims,
    read_freqs,
    read_governor,
    read_govs,
)


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
        if self.user_conf:
            conf_files = sorted(self.user_conf.glob("*.conf"))
            if conf_files:
                self.config.read(conf_files)

    def _read_profiles(self):
        """Read .profile files from configuration directories"""
        # drop-in configuration
        if self.etc_confd.exists():
            profile_files = sorted(self.etc_confd.glob("*.profile"))
            for file in profile_files:
                prof = Profile(file, system=True)
                self._profiles.update({prof.name: prof})

        # user configuration
        if self.user_conf:
            profile_files = sorted(self.user_conf.glob("*.profile"))
            for file in profile_files:
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
        return sorted(self._profiles.keys())

    def get_profile(self, name):
        """Return named profile object
        Args:
            name: Name of the profile

        Returns:
            profile: Profile object

        """
        return self._profiles.get(name)

    def get_profile_index(self, name):
        """Return the index for named profile
        Args:
            name: The name of the profile to find
        Returns:
            index: -1 if not found, position from sorted index otherwise

        """
        if name not in self._profiles:
            return -1

        return sorted(self._profiles).index(name)

    def delete_profile(self, name):
        """Delete profile

        Args:
            name: The profile name

        """
        prof = self._profiles.get(name)
        if prof is not None:
            prof.delete_file()
            del self._profiles[name]

    def create_profile_from_settings(self, name, settings):
        """Creates new profile form settings

        Args:
            name: Name of the profile
            settings: Profile settings

        """
        profile = Profile()
        profile.name = name
        profile.parse_settings(settings)
        if self.user_conf.exists():
            _name = name.replace(" ", "-")
            _name = "cpg-{}.profile".format(_name)
            filename = self.user_conf / _name

        profile.file = filename
        profile.write_file()
        self._profiles[name] = profile

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

    def set(self, section, option, value):
        """Set option under specified section

        Args:
            section: The section to set
            option: The option to set
            value: The value of the option

        """
        self.config[section][option] = str(value)

    def write_settings(self):
        if self.user_conf:
            conf_file = self.user_conf / "00-cpg.conf"
            with conf_file.open("w") as f:
                self.config.write(f)
            return True
        else:
            return False

    def _generate_default_profiles(self):
        """Generate default profiles based on current hardware.
        The two profiles generated are 'Balanced' and 'Performance'.
        The profiles apply either power-saving or performance governor.

        """
        # Get a governor list from first cpu
        govs = read_govs(0)
        if not govs:
            return

        # generate balanced profile based on schedutil/ondemand governor
        if "schedutil" in govs:
            self._profiles["Balanced"] = DefaultProfile(
                "Balanced", "schedutil")
        elif "ondemand" in govs:
            self._profiles["Balanced"] = DefaultProfile(
                "Balanced", "ondemand")

        for gov in govs:
            if gov is not "userspace":
                self._profiles[gov.title()] = DefaultProfile(gov.title(), gov)


class Profile:
    """Wrapper for .profile files"""

    def __init__(self, filename=None, system=False):
        self._custom = True
        self.system = system
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

    def delete_file(self):
        """Delete profile file"""
        if self.file is not None:
            self.file.unlink(missing_ok=True)

    def parse_settings(self, settings):
        for core, conf in settings.items():
            config = {
                "freqs": conf.freqs_scaled,
                "governor": conf.governor,
                "online": conf.online,
            }
            self.settings[core] = config

    def write_file(self):
        if self.file:
            settings = self._format_settings()
            self.file.write_text(settings)

    def _format_settings(self):
        body = "# name: {}\n\n".format(self.name)
        body += "# CPU\tMin\tMax\tGovernor\tOnline\n"
        for core, conf in self.settings.items():
            fmin, fmax = conf["freqs"]
            gov = conf["governor"]
            online = conf["online"]
            line = "{}\t{}\t{}\t{}\t{}\n".format(
                core, int(fmin / 1e3), int(fmax / 1e3), gov, online
            )
            body += line

        return body

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
        self._custom = False
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

    units = {
        "mhz": 1e3,
        "ghz": 1e6,
    }

    def __init__(self, cpu):
        self.cpu = cpu
        self._factor = self.units["mhz"]
        self._settings = {}
        self._new_settings = {}
        # Attributes that don't change
        self._lims = read_freq_lims(cpu)
        self._governors = read_govs(cpu)
        self.energy_pref_avail = is_energy_pref_avail(cpu)
        self.energy_prefs = []
        self.update_conf()

    def update_conf(self):
        cpu = self.cpu
        self._settings["freqs"] = read_freqs(cpu)
        self._settings["governor"] = read_governor(cpu)
        self._settings["online"] = is_online(cpu)
        # In case a new governor has been added
        self._governors = read_govs(cpu)
        # If energy performance preferences are available
        self._settings["energy_pref"] = None

        if self.energy_pref_avail:
            self._settings["energy_pref"] = read_energy_pref(cpu)
            self.energy_prefs = read_available_energy_prefs(cpu)

        self.reset_conf()

    def reset_conf(self):
        # Reset changed values
        self._new_settings = self._settings.copy()

    def reset_energy_pref(self):
        # Reset changed values
        self.energy_pref = self._settings["energy_pref"]

    def setting_changed(self, param):
        ch = False
        if param in self._settings:
            ch = self._settings[param] != self._new_settings[param]
        return ch

    def __repr__(self):
        return "Cpu: {}\nFreqs: {}\nGovernor: {}\n".format(
            self.cpu, self.freqs, self.governor
        )

    @property
    def changed(self):
        return self._settings != self._new_settings

    @property
    def energy_pref_id(self):
        pref = self._new_settings.get("energy_pref")
        if pref:
            return self.energy_prefs.index(pref)
        return -1

    @property
    def energy_pref(self):
        pref = self._new_settings.get("energy_pref")
        return pref

    @energy_pref.setter
    def energy_pref(self, pref):
        conf = self._new_settings
        if isinstance(pref, str):
            conf["energy_pref"] = pref

        if isinstance(pref, int):
            conf["energy_pref"] = self.energy_prefs[pref]

    @property
    def freqs(self):
        freqs = self._new_settings["freqs"]
        f = self._factor
        return freqs[0] / f, freqs[1] / f

    @freqs.setter
    def freqs(self, freqs):
        f = self._factor
        self._new_settings["freqs"] = (int(freqs[0] * f), int(freqs[1] * f))

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
        f = self._factor
        return freqs[0] / f, freqs[1] / f

    @property
    def online(self):
        return self._new_settings.get("online")

    @online.setter
    def online(self, on):
        self._new_settings["online"] = bool(on)

    def set_units(self, unit: str):
        unit = unit.lower()
        if unit not in self.units.keys():
            return
        self._factor = self.units[unit]
