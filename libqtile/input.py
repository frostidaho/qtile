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
