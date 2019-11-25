pkglibdir = join_paths(get_option('prefix'), get_option('libdir'),
                       meson.project_name())

dbus_dir = join_paths(get_option('datadir'), 'dbus-1')

service_conf = configuration_data() 
service_conf.set('pkglibdir', pkglibdir)

systemd_service  = configure_file(
  input: 'cpupower-gui-helper.service.in',
  output: 'cpupower-gui-helper.service',
  configuration: service_conf,
  install: true,
  install_dir: join_paths('/lib', 'systemd', 'system')
)

dbus_service  = configure_file(
  input: 'org.rnd2.cpupower_gui.helper.service.in',
  output: 'org.rnd2.cpupower_gui.helper.service',
  configuration: service_conf,
  install: true,
  install_dir: join_paths(dbus_dir, 'system-services')
)

install_data(
    'org.rnd2.cpupower_gui.helper.conf', 
    install_dir : join_paths(dbus_dir, 'system.d')
)
