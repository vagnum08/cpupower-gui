Name:           cpupower-gui
Version:        0.6.2
Release:        1%{?dist}
Summary:        Cpupower-gui is a graphical program that can change the scaling frequency limits of the cpu

License:        GPLv3+
URL:            https://gitlab.com/vagnum08/cpupower-gui
Source0:        https://gitlab.com/vagnum08/cpupower-gui/uploads/211f0fdb09c1e3fed1a2465484137d0d/cpupower-gui-0.6.2.tar.xz

BuildArch: noarch

BuildRequires:  autoconf, autoconf-archive, automake, tzdata, mawk, gettext, python3, pkg-config, file
Requires:       gtk3, hicolor-icon-theme, polkit-gnome, python3-dbus

%description
This program is designed to allow you to change the frequency limits of your cpu and its governor. The application is similar in functionality to cpupower.

%global debug_package %{nil}

%prep
%autosetup

%build
%configure --libdir %{_exec_prefix}/lib
%make_build


%install
rm -rf $RPM_BUILD_ROOT
%make_install
rm -rf  %{buildroot}%{_exec_prefix}/lib/python3.7/site-packages/cpupower_gui/__pycache__/
%find_lang %{name}


%files
%{_bindir}/cpupower-gui
%{_exec_prefix}/lib/python3.7/site-packages/cpupower_gui/
%{_exec_prefix}/lib/cpupower-gui/
%{_exec_prefix}/lib/systemd/
%{_datadir}/icons/hicolor/scalable/apps/cpupower-gui.svg
%{_datadir}/locale/
%{_datadir}/polkit-1/actions/org.rnd2.cpupower-gui.policy
%{_datadir}/dbus-1/system.d/org.rnd2.cpupower_gui.helper.conf
%{_datadir}/dbus-1/system-services/org.rnd2.cpupower_gui.helper.service
%{_datadir}/applications/cpupower-gui.desktop
%{_datadir}/cpupower-gui/ui/cpupower.glade


%license COPYING 
%doc NEWS AUTHORS



%changelog
* Sun Nov 25 2018 vagnum08 <vagnum08@gmail.com>
- Initial version of the package
