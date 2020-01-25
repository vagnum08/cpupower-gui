pkglibdir = join_paths(get_option('prefix'), get_option('libdir'),
                       meson.project_name())

dbus_dir = join_paths(get_option('datadir'), 'dbus-1')
systemd_dir = get_option('systemddir')

service_conf = configuration_data() 
service_conf.set('pkglibdir', pkglibdir)
service_conf.set('bindir', join_paths(get_option('prefix'),
                                      get_option('bindir')))

systemd_service  = configure_file(
  input: 'cpupower-gui-helper.service.in',
  output: 'cpupower-gui-helper.service',
  configuration: service_conf,
  install: true,
  install_dir: join_paths(systemd_dir, 'system')
)

dbus_service  = configure_file(
  input: 'org.rnd2.cpupower_gui.helper.service.in',
  output: 'org.rnd2.cpupower_gui.helper.service',
  configuration: service_conf,
  install: true,
  install_dir: join_paths(dbus_dir, 'system-services')
)

dbus_service  = configure_file(
  input: 'org.rnd2.cpupower_gui.service.in',
  output: 'org.rnd2.cpupower_gui.service',
  configuration: service_conf,
  install: true,
  install_dir: join_paths(dbus_dir, 'services')
)

install_data(
    'org.rnd2.cpupower_gui.helper.conf', 
    install_dir : join_paths(dbus_dir, 'system.d')
)
