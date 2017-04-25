from . import xcbq

def _make_modifiers_to_masks(xcbq_conn):
    _mask_cache = {}
    d_modmasks, d_keysyms = xcbq.ModMasks, xcbq.keysyms
    keysym_to_keycode = xcbq_conn.keysym_to_keycode
    reverse_modmap = xcbq_conn.reverse_modmap

    def modifiers_to_masks(modifiers):
        cache = _mask_cache

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
    return modifiers_to_masks

# modifiers_to_masks = _make_modifiers_to_masks()
class _Grabber(object):
    def __init__(self, conn, cfg_input, **kwargs):
        self.conn = conn
        self.cfg_input = cfg_input
        sa = setattr
        for k, v in kwargs.items():
            sa(self, k, v)

    def modifiers_to_masks(self, modifiers):
        try:
            fn = self.__modifiers_to_masks
        except AttributeError:
            fn = _make_modifiers_to_masks(self.conn)
            _Grabber.__modifiers_to_masks = staticmethod(fn)
        return list(fn(modifiers))

    @property
    def modmask(self):
        return self.cfg_input.modmask

    @property
    def ignore_modifiers(self):
        try:
            return self._ignore_modifiers
        except AttributeError:
            ignored = (
                ('lock', 'Num_Lock'),
                ('Num_Lock',),
            )
            return ignored

    @ignore_modifiers.setter
    def ignore_modifiers(self, value):
        self._ignore_modifiers = value

    def grab(self, *args, **kwargs):
        raise NotImplementedError('must implement grab()')

    def ungrab(self):
        raise NotImplementedError('must implement ungrab()')


# def grab_key(self, keycode, modifiers, owner_events,
#              pointer_mode, keyboard_mode):
# def grab_button(self, button, modifiers, owner_events,
#                 event_mask, pointer_mode, keyboard_mode):
# def grab_pointer(self, owner_events, event_mask, pointer_mode,
#                  keyboard_mode, cursor=None):
