project('cpupower-gui',
  version: '0.8.0',
  meson_version: '>= 0.50.0',
  default_options: ['warning_level=2',
    'systemddir=/usr/lib/systemd',
    'pkla=false',
    ],
  )

i18n = import('i18n')

application_id = 'org.rnd2.cpupower_gui'
name = meson.project_name()

conf = configuration_data()
conf.set_quoted('GETTEXT_PACKAGE', 'cpupower-gui')
conf.set_quoted('APPLICATION_ID', application_id)

# Common paths
prefix = get_option('prefix')
pkglibdir = join_paths(prefix, get_option('libdir'), name)
dbus_dir = join_paths(get_option('datadir'), 'dbus-1')
systemd_dir = get_option('systemddir')
pkgdatadir = join_paths(prefix, get_option('datadir'), name)
moduledir = join_paths(pkgdatadir, 'cpupower_gui')

subdir('cpupower_gui')
subdir('data')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')

