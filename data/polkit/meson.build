actions_dir = join_paths(get_option('datadir'), 'polkit-1/actions')
rules_dir = join_paths(get_option('datadir'), 'polkit-1/rules.d')
authority_dir = join_paths(get_option('localstatedir'), 
                                      'lib/polkit-1/localauthority/10-vendor.d')

install_data(
    'org.rnd2.cpupower-gui.policy', 
    install_dir : actions_dir
)

if get_option('pkla')
  install_data(
      'org.rnd2.cpupower-gui.pkla',
      install_dir : authority_dir
  )
else
  install_data(
      'org.rnd2.cpupower-gui.rules',
      install_dir : rules_dir
  )
endif
