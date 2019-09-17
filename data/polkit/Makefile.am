#policykit
polkitactionsdir = $(datadir)/polkit-1/actions/
polkitactions_DATA = org.rnd2.cpupower-gui.policy

policykitdir = ${localstatedir}/lib/polkit-1/localauthority/10-vendor.d/
policykit_DATA = org.rnd2.cpupower-gui.pkla

EXTRA_DIST = org.rnd2.cpupower-gui.policy \
             org.rnd2.cpupower-gui.pkla

-include $(top_srcdir)/git.mk
