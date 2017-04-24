from collections import namedtuple as _namedtuple
from libqtile import xcbq
from six.moves import reduce
import operator

_X11Key = _namedtuple('_X11Key', ('code', 'mask', 'cfg_key'))
# _X11Button = _namedtuple('_X11Button', ('code', 'mask', 'cfg_button'))

_X11Input = _namedtuple('_X11Input', ('code', 'mask', 'cfg_obj'))

class Press(object):
    _mask_cache = {}
    def __init__(self, conn, cfg_obj, **kwargs):
        self.conn = conn
        self.cfg_obj = cfg_obj
        self.modmask = cfg_obj.modmask
        sa = setattr
        for k,v in kwargs.items():
            sa(self, k, v)

    @property
    def code(self):
        raise NotImplementedError('need to implement code() property')

    def _strs_to_masks(self, modifiers):
        d_keysyms = xcbq.keysyms
        d_modmasks = xcbq.ModMasks
        cache = self._mask_cache
        keysym_to_keycode = self.conn.keysym_to_keycode
        reverse_modmap = self.conn.reverse_modmap

        for mod in modifiers:
            try:
                yield cache[mod]
                continue
            except KeyError:
                pass

            try:
                val = d_modmasks[mod]
                yield val
                cache[mod] = val
                continue
            except KeyError:
                pass

            _keysym = d_keysyms[mod]
            _keycode = keysym_to_keycode(_keysym)
            _name = reverse_modmap[_keycode]
            if _name:
                val = d_modmasks[_name[0]]
            else:
                val = 0
            yield val
            cache[mod] = val

    def mods_to_mask(self, modifiers):
        or_ = operator.or_
        to_masks = self._strs_to_masks
        return reduce(or_, to_masks(modifiers), 0)

    def get_x11(self, *ignore_modifiers):
        modmask = self.modmask
        X11Input = _X11Input
        cfg_obj = self.cfg_obj
        code = self.code

        yield X11Input(code, modmask, cfg_obj)
        seen_masks = {modmask}
        ignore_masks = []
        for mods in ignore_modifiers:
            if isinstance(mods, str):
                mods = (mods,)
            ignore_masks.append(self.mods_to_mask(mods))
        for mask in ignore_masks:
            new_mask = modmask | mask
            if new_mask in seen_masks:
                continue
            seen_masks.add(new_mask)
            yield X11Input(code, new_mask, cfg_obj)


class _QKey(Press):
    '''A class used by manager.py

    Not intended to be used in your config.py
    '''

    def __init__(self, conn, cfg_key):
        super(_QKey, self).__init__(conn, cfg_key)

        # self.keysym = xcbq.keysyms[cfg_key.key]
        self.keysym = cfg_key.keysym
        self.keycode = conn.keysym_to_keycode(self.keysym)
        # self.modmask = cfg_key.modmask
        # self.modmask = self.mods_to_mask(cfg_key.modifiers)

    @property
    def code(self):
        return self.keycode

    def get_x11_keys(self, *ignore_modifiers):
        for val in self.get_x11(*ignore_modifiers):
            yield val

def x11_keys(xcbq_conn, *cfg_keys):
    QKey = _QKey
    ignore_modifiers = (
        ('lock', 'Num_Lock'),
        ('Num_Lock',),
    )
    for cfg_key in cfg_keys:
        qkey = QKey(xcbq_conn, cfg_key)
        for xkey in qkey.get_x11(*ignore_modifiers):
            yield xkey


class _QClick(Press):
    def __init__(self, conn, cfg_click):
        super(_QClick, self).__init__(conn, cfg_click)

        
