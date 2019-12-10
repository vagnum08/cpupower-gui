# Maintainer: vagnum08 <vagnum08@gmail.com>

pkgname=cpupower-gui
pkgver=0.7.2
pkgrel=1
pkgdesc="A GUI utility to set CPU frequency limits"
arch=(any)
url="https://github.com/vagnum08/cpupower-gui"
license=('GPL')
depends=('python' 'gtk3' 'hicolor-icon-theme' 'polkit' 'python-dbus' 'python-gobject')
optdepends=('polkit-gnome: needed for authentification in Cinnamon, Gnome'
                      'lxsession: needed for authentification in Xfce, LXDE etc.')
makedepends=('meson')
provides=("${pkgname}")
conflicts=("${pkgname}")
source=("${pkgname}_${pkgver}.orig.tar.gz"::"https://github.com/vagnum08/cpupower-gui/archive/v${pkgver}.tar.gz"
               "fix-dbus.patch")
sha256sums=('937898269831531f52a05c1cfffa32274971067dbd8ade806d35022e6e5f356f'
            'f7f2b65596ddaafa5fda63d65bffdb2022e11ed003818fa41ccdb30ca42de418')

prepare() {
    cd "$srcdir/${pkgname}-${pkgver}"
    patch -Np1 -i ../fix-dbus.patch
    # Fix systemd lib path
    sed -i "s@'/lib'@'lib'@" data/services/meson.build
}

build() {
  meson --prefix /usr --buildtype=plain "$srcdir/${pkgname}-${pkgver}" build
  ninja -C build
}

package() {
  DESTDIR="$pkgdir" ninja -C build install
}
