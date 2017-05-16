bin_SCRIPTS = cpupower-gui-pkexec \
              cpupower-gui

cpupower-gui-pkexec: cpupower-gui-pkexec.in
	@$(MKDIR_P) bin
	$(AM_V_GEN)$(SED)                       \
		-e s!\@localedir\@!$(localedir)!    \ 
		-e s!\@pythondir\@!$(pythondir)!    \
		-e s!\@PYTHON\@!$(PYTHON)!          \
		< $< > $@
	@chmod a+x $@

BUILD_SOURCES = $(bin_SCRIPTS)
EXTRA_DIST = cpupower-gui-pkexec.in \
             cpupower-gui


-include $(top_srcdir)/git.mk
