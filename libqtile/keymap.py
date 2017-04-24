from collections import namedtuple as _namedtuple
from libqtile import xcbq
from six.moves import reduce
import operator

_X11Key = _namedtuple('_X11Key', ('code', 'mask', 'cfg_key'))


class _QKey(object):
    '''A class used by manager.py

    Not intended to be used in your config.py
    '''

    def __init__(self, conn, cfg_key):
        self.conn = conn
        self.cfg_key = cfg_key

        # self.keysym = xcbq.keysyms[cfg_key.key]
        self.keysym = cfg_key.keysym
        self.keycode = conn.keysym_to_keycode(self.keysym)
        self.modmask = cfg_key.modmask
        # self.modmask = self.mods_to_mask(*cfg_key.modifiers)

    def _strs_to_masks(self, modifiers):
        d_keysyms = xcbq.keysyms
        d_modmasks = xcbq.ModMasks
        keysym_to_keycode = self.conn.keysym_to_keycode
        reverse_modmap = self.conn.reverse_modmap
        for mod in modifiers:
            print('mod', mod)
            try:
                yield d_modmasks[mod]
            except KeyError:
                _keysym = d_keysyms[mod]
                _keycode = keysym_to_keycode(_keysym)
                print('keysym', _keysym, 'keycode', _keycode)
                _name = reverse_modmap[_keycode]
                print('_name', _name)
                if _name:
                    yield d_modmasks[_name[0]]
                else:
                    yield 0

    def mods_to_mask(self, *modifiers):
        or_ = operator.or_
        to_masks = self._strs_to_masks
        try:
            return reduce(or_, to_masks(modifiers))
        except TypeError:
            return 0

    def get_x11_keys(self, *ignore_modifiers):
        keycode = self.keycode
        modmask = self.modmask
        X11Key = _X11Key
        cfg_key = self.cfg_key

        yield X11Key(keycode, modmask, cfg_key)
        seen_masks = {modmask}
        # TODO ignore masks should be some sort of permutation
        # of all of the ignore modifiers
        ignore_masks = []
        for mods in ignore_modifiers:
            if isinstance(mods, str):
                mods = (mods,)
            ignore_masks.append(self.mods_to_mask(*mods))
        for mask in ignore_masks:
            new_mask = modmask | mask
            if new_mask in seen_masks:
                continue
            seen_masks.add(new_mask)
            yield X11Key(keycode, new_mask, cfg_key)


def x11_keys(xcbq_conn, *cfg_keys):
    QKey = _QKey
    ignore_modifiers = (
        ('lock', 'Num_Lock'),
        ('Num_Lock',),
    )
    for cfg_key in cfg_keys:
        qkey = QKey(xcbq_conn, cfg_key)
        for xkey in qkey.get_x11_keys(*ignore_modifiers):
            yield xkey
