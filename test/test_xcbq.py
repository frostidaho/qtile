import pytest
from xvfbwrapper import Xvfb
import xcffib
from libqtile import xcbq

@pytest.fixture(scope='function', autouse=True)
def xdisplay(request):
    xvfb = Xvfb(width=1280, height=720)
    xvfb.start()
    display = ':{}'.format(xvfb.new_display)
    yield display
    xvfb.stop()

def test_new_window(xdisplay):
    conn = xcbq.Connection(xdisplay)
    win = conn.create_window(1, 2, 640, 480)
    assert isinstance(win, xcbq.Window)
    geom = win.get_geometry()
    assert geom.x == 1
    assert geom.y == 2
    assert geom.width == 640
    assert geom.height == 480
    win.kill_client()
    with pytest.raises(xcffib.ConnectionException):
        win.get_geometry()

def test_net_wm_states(xdisplay):
    conn = xcbq.Connection(xdisplay)
    win = conn.create_window(1, 1, 640, 480)
    assert isinstance(win, xcbq.Window)
    attr_name = lambda x: x.lstrip('_').lower()
    names = [attr_name(x) for x in xcbq.net_wm_states]

    for name in names:
        val = getattr(win, name)
        assert val is False
        setattr(win, name, True)
        val = getattr(win, name)
        assert val is True
    
    for name in names:
        assert getattr(win, name) is True
