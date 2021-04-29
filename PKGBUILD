pkgname=python3-fildem
pkgver=0.6.5
pkgrel=1
pkgdesc="This project is a fork of gnomehud with the adition of a global menu bar"
arch=('i686' 'x86_64')
url="https://github.com/gonzaarcr/fildem"
depends=('bamf'
         'appmenu-gtk-module'
         'libkeybinder3'
         'libdbusmenu-gtk2'
         'libdbusmenu-gtk3')
makedepends=('git')
provides=("python3-fildem=$pkgver")
source=('git+https://github.com/gonzaarcr/fildem.git')
md5sums=('SKIP')

pkgver() {
    cd "$srcdir/fildem"
    python3 -c "import fildem; print(fildem.__version__)"
}

build() {
    cd "$srcdir/fildem"
    python3 setup.py bdist_wheel
}

check() {
    cd "$srcdir/fildem"
    python3 setup.py test
}

package() {
    cd "$srcdir/fildem"
    python3 setup.py install --skip-build --root=$pkgdir --optimize=1
}
