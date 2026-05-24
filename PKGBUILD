# Maintainer: pack-test
pkgname=myapp-test
pkgver=1.0.0
pkgrel=1
pkgdesc='Packaging test application - CI verification only'
arch=('x86_64')
url='https://github.com/Kindness-Kismet/pack-test'
license=('MIT')

package() {
    mkdir -p "$pkgdir/usr/bin"
    echo '#!/bin/sh' > "$pkgdir/usr/bin/myapp"
    echo 'echo hello' >> "$pkgdir/usr/bin/myapp"
    chmod 755 "$pkgdir/usr/bin/myapp"
}
