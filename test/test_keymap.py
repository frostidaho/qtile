import pytest
from libqtile import keymap
from libqtile import config
from libqtile import xcbq


@pytest.fixture(scope='module', autouse=True)
def xdisplay(request):
    from xvfbwrapper import Xvfb
    xvfb = Xvfb(width=1280, height=720)
    xvfb.start()
    display = ':{}'.format(xvfb.new_display)
    yield display
    xvfb.stop()

@pytest.fixture(scope='function')
def xcbq_conn(xdisplay):
    conn = xcbq.Connection(xdisplay)
    conn.flush()
    conn.xsync()
    yield conn
    conn.disconnect()

def ex_func(*args, **kwargs):
    pass

def test_qkey_strs_to_masks(xcbq_conn):
    key = config.Key(['mod4', 'shift'], 't', ex_func)
    qkey = keymap.QKey(xcbq_conn, key)

    d_mods = xcbq.ModMasks
    strs_to_masks = qkey._strs_to_masks
    for key,val in d_mods.items():
        assert val == next(strs_to_masks([key,]))

    numlock_mask = next(strs_to_masks(['Num_Lock',]))
    assert numlock_mask == 16 or numlock_mask == 0


def test_x11_keys(xcbq_conn):
    key = config.Key(['mod4', 'shift'], 't', ex_func)
    qkey = keymap.QKey(xcbq_conn, key)

    for val in qkey.get_x11_keys():
        assert isinstance(val, keymap._X11Key)
        assert val.code == xcbq_conn.keysym_to_keycode(xcbq.keysyms['t'])
        assert val.mask & (64 | 1) == val.mask
    
