bin_SCRIPTS = cpupower-gui

cpg_pkglibdir = $(pkglibdir)
cpg_pkglib_SCRIPTS = cpupower-gui-helper

cpupower-gui: cpupower-gui.in
	$(AM_V_GEN)$(SED)                             \
		-e s!\@localedir\@!$(localedir)!     \
		-e s!\@PYTHON\@!$(PYTHON)!       \
		-e s!\@pkgdatadir\@!$(pkgdatadir)!  \
		-e s!\@VERSION\@!$(VERSION)!   \
		< $< > $@
	@chmod a+x $@

cpupower-gui-helper: cpupower-gui-helper.py.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@localedir\@!$(localedir)!    \
		-e s!\@PYTHON\@!$(PYTHON)!          \
		< $< > $@
	@chmod a+x $@

EXTRA_DIST = cpupower-gui.in \
             cpupower-gui-helper.py.in

CLEANFILES = $(BUILD_SOURCES)

-include $(top_srcdir)/git.mk
