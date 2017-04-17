import pytest
from xvfbwrapper import Xvfb
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

def test_net_wm_states(xdisplay):
    conn = xcbq.Connection(xdisplay)
    win = conn.create_window(1, 1, 640, 480)
    assert isinstance(win, xcbq.Window)
    for name in xcbq.net_wm_states:
        lower_name = name.lstrip('_').lower()
        val = getattr(win, lower_name)
        assert val is False
        setattr(win, lower_name, True)
        val = getattr(win, lower_name)
        assert val is True
    
