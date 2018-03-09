#systemd
systemddir = $(libdir)/systemd/system/
systemd_DATA = cpupower-gui-helper.service

cpupower-gui-helper.service: cpupower-gui-helper.service.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@pkglibdir\@!$(pkglibdir)!   \
		< $< > $@

EXTRA_DIST = cpupower-gui-helper.service.in

CLEANFILES = $(systemd_DATA)

-include $(top_srcdir)/git.mk
