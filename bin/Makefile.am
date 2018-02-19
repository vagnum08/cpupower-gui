bin_SCRIPTS = cpupower-gui \
              cpupower-gui-helper

cpupower-gui: cpupower-gui.py.in
	@$(MKDIR_P) bin
	$(AM_V_GEN)$(SED)                       \
		-e s!\@localedir\@!$(localedir)!    \ 
		-e s!\@pythondir\@!$(pythondir)!    \
		-e s!\@PYTHON\@!$(PYTHON)!          \
		< $< > $@
	@chmod a+x $@

cpupower-gui-helper: cpupower-gui-helper.py.in
	@$(MKDIR_P) bin
	$(AM_V_GEN)$(SED)                       \
		-e s!\@localedir\@!$(localedir)!    \
		-e s!\@pythondir\@!$(pythondir)!    \
		-e s!\@PYTHON\@!$(PYTHON)!          \
		< $< > $@
	@chmod a+x $@

BUILD_SOURCES = $(bin_SCRIPTS)
EXTRA_DIST = cpupower-gui.py.in \
             cpupower-gui-helper.py.in


-include $(top_srcdir)/git.mk
