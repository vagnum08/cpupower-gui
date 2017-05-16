#the ui file
uidir = $(datadir)/cpupower-gui/ui
ui_DATA = cpupower.glade

#the application icon
appicondir = $(datadir)/icons/hicolor/scalable/apps
appicon_DATA = cpupower-gui.svg

#the .desktop file
desktopdir = $(datadir)/applications
desktop_DATA = cpupower-gui.desktop

#policykit
polkitdir = $(datadir)/polkit-1/actions/
polkit_DATA = org.rnd2.pkexec.run-cpupower-gui.policy

EXTRA_DIST = org.rnd2.pkexec.run-cpupower-gui.policy \
             cpupower.glade \
             cpupower-gui.desktop.in \
             cpupower-gui.svg

cpupower-gui.desktop: cpupower-gui.desktop.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@prefix\@!$(bindir)!    \ 
		< $< > $@


-include $(top_srcdir)/git.mk
