mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
project_dir := $(dir $(mkfile_path))
build_dir := $(project_dir)tmp_build
.PHONY: all install clean quick

all:
	sh "$(project_dir)build.sh"

install: all
	sudo pacman -U $(project_dir)qtile-*.pkg.tar.xz

# http://stackoverflow.com/a/3801342
clean:
	git clean -dxf

quick: clean all
	sudo pacman --noconfirm -U $(project_dir)qtile-*.pkg.tar.xz
