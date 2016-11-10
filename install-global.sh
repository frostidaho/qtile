#!/usr/bin/bash
# Getting script directory: http://stackoverflow.com/a/246128
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo pip3 install --no-deps --install-option="--optimize=2" "$DIR"
sudo cp "$DIR/resources/qtile.desktop" /usr/share/xsessions/qtile.desktop
