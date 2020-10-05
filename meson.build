project('cpupower-gui',
  version: '0.8.0',
  meson_version: '>= 0.50.0',
  default_options: ['warning_level=2',
    'systemddir=/usr/lib/systemd',
    ],
  )

prefix = get_option('prefix')

i18n = import('i18n')

application_id = 'org.rnd2.cpupower_gui'

conf = configuration_data()
conf.set_quoted('GETTEXT_PACKAGE', 'cpupower-gui')
conf.set_quoted('APPLICATION_ID', application_id)


subdir('data')
subdir('cpupower_gui')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')

