%define debug_package %nil

Name: 		cpupower-gui
Version: 	0.6.2
Release:  	%mkrel 1
Summary: 	GUI utility to change the CPU frequency
License: 	GPL
URL:		https://github.com/vagnum08/cpupower-gui
Group: 		System/Kernel and hardware
Source: 	%name-%version.tar.xz
Distribution: 	blackPanther OS
Packager:	Charles K Barcza
Requires: 	python3-dbus python3-gobject3

%description
This utility can change the operating frequency of the CPU for each 
core separately. Additionally, the cpu governor can be changed.

%prep
%setup -q

%build
[ ! -f configure ] && ./autogen.sh
%configure2_5x

%install
%make_install

mkdir -p %buildroot/%_unitdir
# fix wrong path on blackPanther OS
mv %buildroot%_libdir/systemd/system/* %buildroot%_unitdir
# clean unnecessary dir 
rm -rf %buildroot%_libdir/systemd/

%files
%doc AUTHORS *.md ABOUT-NLS NEWS
%license COPYING
%_bindir/cpupower-gui
%_libdir/cpupower-gui/cpupower-gui-helper
%_datadir/applications/cpupower-gui.desktop
%_datadir/cpupower-gui/ui/cpupower.glade
%_datadir/dbus-1/system-services/org.rnd2.cpupower_gui.helper.service
%_datadir/dbus-1/system.d/org.rnd2.cpupower_gui.helper.conf
%_datadir/icons/hicolor/scalable/apps/cpupower-gui.svg
%_datadir/locale/*/LC_MESSAGES/cpupower-gui.mo
%_datadir/polkit-1/actions/org.rnd2.cpupower-gui.policy
%python3_sitelib/cpupower_gui
%_unitdir/cpupower-gui-helper.service

%changelog
* Mon Jun 24 2019 Charles K. Barcza <info@blackpanther.hu> 0.6.2-1bP
- build package for blackPanther OS v17-19.x 32/64 bit
- initial package
------------------------------------------------------------------------


