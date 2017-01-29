#!/usr/bin/bash
# Getting script directory: http://stackoverflow.com/a/246128
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pip3 install --user -r "$DIR/requirements.txt"
pip3 install --user --no-deps --install-option="--optimize=2" "$DIR"
sudo cp "$DIR/resources/qtile.desktop" /usr/share/xsessions/qtile.desktop
