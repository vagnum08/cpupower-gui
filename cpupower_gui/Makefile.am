moduledir = $(pythondir)/cpupower_gui
module_PYTHON = __main__.py

EXTRA_DIST = __main__.py.in

__main__.py: __main__.py.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@datadir\@!$(datadir)!   \
		< $< > $@
	@chmod a+x $@

CLEANFILES = $(module_PYTHON)

-include $(top_srcdir)/git.mk
