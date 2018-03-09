#the .desktop file
desktopdir = $(datadir)/applications
desktop_DATA = cpupower-gui.desktop

EXTRA_DIST = cpupower-gui.desktop.in

cpupower-gui.desktop: cpupower-gui.desktop.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@prefix\@!$(bindir)!    \
		< $< > $@

CLEANFILES = $(desktop_DATA)

-include $(top_srcdir)/git.mk
