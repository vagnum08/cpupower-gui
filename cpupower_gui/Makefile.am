moduledir = $(pythondir)/cpupower_gui
module_PYTHON = __main__.py


__main__.py: __main__.py.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@datadir\@!$(datadir)!   \
		< $< > $@
	@chmod a+x $@
	
-include $(top_srcdir)/git.mk
