import pytest
import py
import os
from libqtile.widget import Battery, BatteryIcon
from libqtile import images
import cairocffi

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(TEST_DIR), 'data')

audio_volume_muted = os.path.join(
    DATA_DIR, 'svg', 'audio-volume-muted.svg',
)

audio_volume_muted = py.path.local(audio_volume_muted)

def test_images_fail():
    battery = BatteryIcon(theme_path=TEST_DIR)
    with pytest.raises(images.LoadingError):
        battery.setup_images()

def test_images_good(tmpdir, fake_bar):
    for name in BatteryIcon.icon_names:
        target = tmpdir.join(name + '.svg')
        audio_volume_muted.copy(target)

    batt = BatteryIcon(theme_path=str(tmpdir))
    batt.fontsize = 12
    batt.bar = fake_bar
    batt.setup_images()
    assert len(batt.surfaces) == len(BatteryIcon.icon_names)
    for name, surfpat in batt.surfaces.items():
        assert isinstance(surfpat, cairocffi.SurfacePattern)
