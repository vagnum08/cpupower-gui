#dbus-1
dbusdir = $(datadir)/dbus-1/system-services/
dbus_DATA = org.rnd2.cpupower_gui.helper.service

dbusconfdir = $(datadir)/dbus-1/system.d/
dbusconf_DATA = org.rnd2.cpupower_gui.helper.conf


org.rnd2.cpupower_gui.helper.service: org.rnd2.cpupower_gui.helper.service.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@pkglibdir\@!$(pkglibdir)!   \
		< $< > $@

EXTRA_DIST = org.rnd2.cpupower_gui.helper.service.in \
	     org.rnd2.cpupower_gui.helper.conf

CLEANFILES = $(dbus_DATA)

-include $(top_srcdir)/git.mk
