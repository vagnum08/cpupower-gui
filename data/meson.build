# Icons
icondir = join_paths('icons', 'hicolor', 'scalable', 'apps')

install_data(
  join_paths(icondir, 'cpupower-gui.svg'),
  install_dir: join_paths(get_option('datadir'), icondir),
  rename: '@0@.svg'.format(application_id)
)

# Desktop configuration
desktop_conf = configuration_data()
desktop_conf.set('icon', application_id)

desktop_file = i18n.merge_file(
  'desktop',
   input: configure_file(
    input: files('org.rnd2.cpupower_gui.desktop.in.in'),
    output: 'org.rnd2.cpupower_gui.desktop.in',
    configuration: desktop_conf
  ),
  output: 'org.rnd2.cpupower_gui.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif

# Appstream metadata
appstream_file = i18n.merge_file(
  input: 'org.rnd2.cpupower_gui.appdata.xml.in',
  output: 'org.rnd2.cpupower_gui.appdata.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate', appstream_file]
  )
endif

# Gschemas
install_data('org.rnd2.cpupower_gui.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

# System configuration
install_subdir('cpupower_gui.d', install_dir: get_option('sysconfdir'))
install_data('cpupower_gui.conf', install_dir: get_option('sysconfdir'))

# Kernel modules configuration for extra governors
install_data('scaling-governors.conf', install_dir: pkgdatadir)

subdir('services')
subdir('polkit')
