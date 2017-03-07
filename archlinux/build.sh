#!/usr/bin/bash
# This script builds an Arch Linux package for Qtile

# Real path to current directory
# http://stackoverflow.com/a/246128
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
BUILDDIR="$DIR/tmp_build"

mkdir -p "$BUILDDIR"
PKGVER="$(git rev-list --count HEAD).$(git rev-parse --short HEAD)"
sed -e "s/@@PKGVER@@/$PKGVER/g" "$DIR/PKGBUILD.template" > "$BUILDDIR/PKGBUILD"
cp "$DIR/"qtile*.install "$BUILDDIR"

buildpkg () {
    echo "Creating Qtile pacman package with git version $PKGVER"
    cd "$BUILDDIR"
    makepkg -s -f
    mv qtile*.pkg.tar.xz "$DIR"
}

buildpkg

