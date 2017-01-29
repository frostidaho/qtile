# Maintainer: frostidaho@gmail.com

pkgname=qtile-py3ida-git
pkgver=2655.82483c7
pkgrel=1
pkgdesc="Python3 full-featured, pure-Python tiling window manager. (git version)"
arch=('any')
url="http://www.qtile.org"
license=('MIT')
depends=('python' 'pango' 'python-xcffib>=0.1.10' 'python-cairocffi' 'python-six' 'python-setproctitle')
makedepends=('python-setuptools' 'git')
# optdepends=('python-setproctitle: change the process name to qtile')
provides=('qtile')
conflicts=('qtile')
install=${pkgname}.install
source=()
md5sums=()

prepare() {
	ln -snf "$startdir" "$srcdir/$pkgname"
}

pkgver() {
  echo $(git rev-list --count HEAD).$(git rev-parse --short HEAD)
}

package() {
  cd $srcdir/$pkgname
  msg "Copying license..."
  install -D -m 644 LICENSE $pkgdir/usr/share/licenses/$pkgname/LICENSE

  msg "Copying default config..."
  install -D -m 644 libqtile/resources/default_config.py $pkgdir/usr/share/doc/$pkgname/default_config.py

  msg "Copying desktop file..."
  install -D -m 644 resources/qtile.desktop $pkgdir/usr/share/xsessions/qtile.desktop

  msg "Running setup.py"
  python setup.py install --root=${pkgdir} --prefix=/usr --optimize=1
}
