#!/bin/bash
# Getting script directory: http://stackoverflow.com/a/246128
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pip install --user --editable "$DIR"
sudo cp "$DIR/resources/qtile.desktop" /usr/share/xsessions/qtile.desktop
