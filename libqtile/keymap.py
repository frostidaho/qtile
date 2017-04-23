from collections import namedtuple as _namedtuple
from libqtile import xcbq
from six.moves import reduce
import operator

_X11Key = _namedtuple('_X11Key', ('code', 'mask'))

class QKey(object):
    '''A class used by manager.py

    Not intended to be used in your config.py
    '''
    def __init__(self, conn, cfg_key):
        self.conn = conn
        self.cfg_key = cfg_key

        self.keysym = xcbq.keysyms[cfg_key.key]
        self.keycode = conn.keysym_to_keycode(self.keysym)
        self.modmask = self.mods_to_mask(*cfg_key.modifiers)


    def _strs_to_masks(self, modifiers):
        d_keysyms = xcbq.keysyms
        d_modmasks = xcbq.ModMasks
        keysym_to_keycode = self.conn.keysym_to_keycode
        reverse_modmap = self.conn.reverse_modmap
        for mod in modifiers:
            try:
                yield d_modmasks[mod]
            except KeyError:
                _keysym = d_keysyms[mod]
                _keycode = keysym_to_keycode(_keysym)
                _name = reverse_modmap[_keycode]
                yield d_modmasks[_name]

    def mods_to_mask(self, *modifiers):
        or_ = operator.or_
        to_masks = self._strs_to_masks
        reduce(or_, to_masks(modifiers))

    def __iter__(self, *ignore_modifiers):
        keycode = self.keycode
        modmask = self.modmask
        X11Key = _X11Key

        yield X11Key(keycode, modmask)
        seen_masks = {modmask}
        ignore_masks = mods_to_mask(ignore_modifiers)
        for mask in ignore_masks:
            new_mask = modmask | mask
            if new_mask in seen_masks:
                continue
            seen_masks.add(new_mask)
            yield X11Key(keycode, new_mask)



