bin_SCRIPTS = cpupower-gui

cpg_pkglibdir = $(pkglibdir)
cpg_pkglib_SCRIPTS = cpupower-gui-helper

cpupower-gui: cpupower-gui.py.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@localedir\@!$(localedir)!    \
		-e s!\@pythondir\@!$(pythondir)!    \
		-e s!\@PYTHON\@!$(PYTHON)!          \
		< $< > $@
	@chmod a+x $@

cpupower-gui-helper: cpupower-gui-helper.py.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@localedir\@!$(localedir)!    \
		-e s!\@pythondir\@!$(pythondir)!    \
		-e s!\@PYTHON\@!$(PYTHON)!          \
		< $< > $@
	@chmod a+x $@

BUILD_SOURCES = $(bin_SCRIPTS) $(cpg_pkglib_SCRIPTS)

EXTRA_DIST = cpupower-gui.py.in \
             cpupower-gui-helper.py.in

CLEANFILES = $(BUILD_SOURCES)

-include $(top_srcdir)/git.mk
