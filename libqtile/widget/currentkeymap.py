# -*- coding: utf-8 -*-
from . import base
from .. import bar, hook


class CurrentKeyMap(base._TextBox):
    """Displays the active Qtile keymap"""

    defaults = [
        ('fallback_text', 'keymap.name err', 'Text displayed when keymap has no name attribute'),
    ]
    orientations = base.ORIENTATION_HORIZONTAL

    def __init__(self, width=bar.CALCULATED, **config):
        base._TextBox.__init__(self, "", width, **config)
        self.add_defaults(CurrentKeyMap.defaults)

    def _configure(self, qtile, bar):
        base._TextBox._configure(self, qtile, bar)
        self.keymap_update(qtile.config.keys)
        hook.subscribe.keymap_change(self.keymap_update)

    def keymap_update(self, keymap):
        try:
            self.text = keymap.name
        except AttributeError:
            self.text = self.fallback_text
        self.bar.draw()
