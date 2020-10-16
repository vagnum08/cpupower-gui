service_conf = configuration_data()
service_conf.set('pkglibdir', pkglibdir)
service_conf.set('helperdir', helperdir)
service_conf.set('bindir', join_paths(prefix,
                                      get_option('bindir')))

helper_systemd_service  = configure_file(
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

# SystemD system unit to apply config at boot
systemd_service  = configure_file(
  input: 'cpupower-gui.service.in',
  output: 'cpupower-gui.service',
  configuration: service_conf,
  install: true,
  install_dir: join_paths(systemd_dir, 'system')
)

# SystemD user unit to apply config at login
systemd_service  = configure_file(
  input: 'cpupower-gui-user.service.in',
  output: 'cpupower-gui-user.service',
  configuration: service_conf,
  install: true,
  install_dir: join_paths(prefix, 'lib/systemd/user')
)
