cpupower-gui
--------------------

This program is designed to allow you to change the frequency limits of your cpu and its governor. The application is similar in functionality to `cpupower`.

# Screenshot

![screenshot](./screenshot.png  "Screenshot")

# Packages
Cpupower-gui is available on the official repositories for a few distributions.

[![Packaging status](https://repology.org/badge/vertical-allrepos/cpupower-gui.svg)](https://repology.org/metapackage/cpupower-gui/versions)

Prebuilt binary packages for Arch, Debian/Rasbian, Fedora, and Ubuntu are available on [openSUSE Build Service](https://software.opensuse.org//download.html?project=home%3Aerigas%3Acpupower-gui&package=cpupower-gui)

## Repositories:

### Arch Linux and derivatives
Packages exist in AUR as [`cpupower-gui`](https://aur.archlinux.org/packages/cpupower-gui/) ([`cpupower-gui-git`](https://aur.archlinux.org/packages/cpupower-gui-git/)), built from this repo.


### blackPanther OS 

```
updating repos
installing cpupower-gui
```
###

### Ubuntu
Packages for Ubuntu can be installed from the following ppa: [ppa:erigas/cpupower-gui](https://launchpad.net/~erigas/+archive/ubuntu/cpupower-gui).

To add the ppa to the system:
```bash
sudo add-apt-repository ppa:erigas/cpupower-gui
sudo apt-get update
```
And install using:
```bash
sudo apt-get install cpupower-gui
```

# Manual Instalation
## Install
To install this program do the following:

- Install missing dependencies (see below)
- Clone the repository
- Change directory to the cloned repo
- Open a terminal in that directory and run `./autogen.sh --prefix=/usr` followed by `make && make install`.

## Uninstall

To uninstall run `make uninstall`.

# Dependencies
## Arch Linux and derivatives
Build:
`pkg-config`, `autoconf-archive`, `git`, `autoconf`, `make`

Runtime:
`python`, `gtk3`, `hicolor-icon-theme`, `polkit`, `python-dbus`, `python-gobject`

## blackPanther OS and derivatives
Build:
`pkg-config`, `autoconf-archive`, `git`, `autoconf`, `make`

Runtime:
`python3`, `gtk3`, `hicolor-icon-theme`, `polkit`, `python3-dbus`, `python3-gobject3`

Install:
`updating repos`
`installing cpupower-gui`

Find in menu and click to start...

## Debian and derivatives
Build:
`autoconf`, `autoconf-archive`, `automake`, `tzdata`, `mime-support`, `mawk`, `gettext`, `python3`, `pkg-config`, `file`

Runtime:
`libgtk-3-0`, `gir1.2-gtk-3.0`, `hicolor-icon-theme`, `policykit-1`, `python3-dbus`
