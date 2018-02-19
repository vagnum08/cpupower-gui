#the ui file
uidir = $(datadir)/cpupower-gui/ui
ui_DATA = cpupower.glade

EXTRA_DIST = cpupower.glade

cpupower.glade: cpupower.glade.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@MAJOR_VERSION\@!$(MAJOR_VERSION)!   \
		-e s!\@MINOR_VERSION\@!$(MINOR_VERSION)!   \
		-e s!\@MICRO_VERSION\@!$(MICRO_VERSION)!   \
		< $< > $@


-include $(top_srcdir)/git.mk
