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

def test_qkey_utils(xcbq_conn):
    key = config.Key(['mod4', 'shift'], 't', ex_func)
    qkey = keymap.QKey(xcbq_conn, key)

    d_mods = {'mod4': 64, 'shift': 1}
    strs_to_masks = qkey._strs_to_masks
    for key,val in d_mods.items():
        assert val == next(strs_to_masks([key,]))


