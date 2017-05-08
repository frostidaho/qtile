# -*- coding: utf-8 -*-
# Copyright (c) 2011 Florian Mounier
# Copyright (c) 2011 Kenji_Takahashi
# Copyright (c) 2012 roger
# Copyright (c) 2012, 2014 Tycho Andersen
# Copyright (c) 2012 Maximilian Köhl
# Copyright (c) 2013 Craig Barnes
# Copyright (c) 2014 Sean Vig
# Copyright (c) 2014 Adi Sieker
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import division

from . import base
from .. import bar, hook
from ..log_utils import logger
import six
import os
from ..layout.base import Layout
from .. import layout as layout_module


class CurrentLayout(base._TextBox):
    """
    Display the name of the current layout of the current group of the screen,
    the bar containing the widget, is on.
    """
    orientations = base.ORIENTATION_HORIZONTAL

    def __init__(self, width=bar.CALCULATED, **config):
        base._TextBox.__init__(self, "", width, **config)

    def _configure(self, qtile, bar):
        base._TextBox._configure(self, qtile, bar)
        self.text = self.bar.screen.group.layouts[0].name
        self.setup_hooks()

    def setup_hooks(self):
        def hook_response(layout, group):
            if group.screen is not None and group.screen == self.bar.screen:
                self.text = layout.name
                self.bar.draw()
        hook.subscribe.layout_change(hook_response)

    def button_press(self, x, y, button):
        if button == 1:
            self.qtile.cmd_next_layout()
        elif button == 2:
            self.qtile.cmd_prev_layout()


class CurrentLayoutIcon(base._TextBox):
    """
    Display the icon representing the current layout of the
    current group of the screen on which the bar containing the widget is.

    If you are using custom layouts, a default icon with question mark
    will be displayed for them. If you want to use custom icon for your own
    layout, for example, `FooGrid`, then create a file named
    "layout-foogrid.png" and place it in `~/.icons` directory. You can as well
    use other directories, but then you need to specify those directories
    in `custom_icon_paths` argument for this plugin.

    The order of icon search is:

    - dirs in `custom_icon_paths` config argument
    - `~/.icons`
    - built-in qtile icons
    """
    orientations = base.ORIENTATION_HORIZONTAL

    defaults = [
        (
            'scale',
            1,
            'Scale factor relative to the bar height.  '
            'Defaults to 1'
        ),
        (
            'custom_icon_paths',
            [],
            'List of folders where to search icons before'
            'using built-in icons or icons in ~/.icons dir.  '
            'This can also be used to provide'
            'missing icons for custom layouts.  '
            'Defaults to empty list.'
        )
    ]

    def __init__(self, **config):
        base._TextBox.__init__(self, "", **config)
        self.add_defaults(CurrentLayoutIcon.defaults)

        self.length_type = bar.STATIC
        self.length = 0

    def _configure(self, qtile, bar):
        base._TextBox._configure(self, qtile, bar)
        self.text = self.bar.screen.group.layouts[0].name
        self.current_layout = self.text
        self.icons_loaded = False
        self.icon_paths = []
        self.surfaces = {}
        self._update_icon_paths()
        self._setup_images()
        self._setup_hooks()

    def _setup_hooks(self):
        """
        Listens for layout change and performs a redraw when it occurs.
        """
        def hook_response(layout, group):
            if group.screen is not None and group.screen == self.bar.screen:
                self.current_layout = layout.name
                self.bar.draw()
        hook.subscribe.layout_change(hook_response)

    def button_press(self, x, y, button):
        if button == 1:
            self.qtile.cmd_next_layout()
        elif button == 2:
            self.qtile.cmd_prev_layout()

    def draw(self):
        if self.icons_loaded:
            try:
                surface = self.surfaces[self.current_layout]
            except KeyError:
                logger.error('No icon for layout {}'.format(
                    self.current_layout
                ))
            else:
                self.drawer.clear(self.background or self.bar.background)
                self.drawer.ctx.set_source(surface)
                self.drawer.ctx.paint()
                self.drawer.draw(offsetx=self.offset, width=self.length)
        else:
            # Fallback to text
            self.text = self.current_layout[0].upper()
            base._TextBox.draw(self)

    def _get_layout_names(self):
        """
        Returns the list of lowercased strings for each available layout name.
        """
        return [
            layout_class_name.lower()
            for layout_class, layout_class_name
            in map(lambda x: (getattr(layout_module, x), x), dir(layout_module))
            if isinstance(layout_class, six.class_types) and issubclass(layout_class, Layout)
        ]

    def _update_icon_paths(self):
        self.icon_paths = []

        # We allow user to override icon search path
        self.icon_paths.extend(self.custom_icon_paths)

        # We also look in ~/.icons/
        self.icon_paths.append(os.path.expanduser('~/.icons'))

        # Default icons are in libqtile/resources/layout-icons.
        # If using default config without any custom icons,
        # this path will be used.
        root = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-2])
        self.icon_paths.append(os.path.join(root, 'resources', 'layout-icons'))

    def _setup_images(self):
        """
        Loads layout icons.
        """
        from ..images import Loader
        img_names = ['layout-{}'.format(x) for x in self._get_layout_names()]
        d_imgs = Loader(*self.icon_paths)(*img_names)
        for img_name, img in d_imgs.items():
            layout_name = img_name.lstrip('layout-')
            new_height = self.bar.height - 1
            img.resize(height=new_height * self.scale)
            if img.width > self.length:
                self.length = int(img.width + self.actual_padding * 2)
            self.surfaces[layout_name] = img.pattern
        self.icons_loaded = True
