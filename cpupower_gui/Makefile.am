moduledir = $(datadir)/cpupower-gui/cpupower_gui
resourcedir = $(datadir)/cpupower-gui/
module_DATA = __init__.py main.py window.py 
resource_DATA = cpupower-gui.gresource

EXTRA_DIST = main.py window.glade.in window.py \
	window.glade.in cpupower_gui.gresource.xml

window.glade: window.glade.in
	$(AM_V_GEN)$(SED)                       \
		-e s!\@VERSION\@!$(VERSION)!   \
		< $< > $@

cpupower-gui.gresource: cpupower_gui.gresource.xml window.glade
	$(AM_V_GEN)glib-compile-resources \
		--target=$@ $<

		
CLEANFILES = cpupower-gui.gresource window.glade

-include $(top_srcdir)/git.mk
