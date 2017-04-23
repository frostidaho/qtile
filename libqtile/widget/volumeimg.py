import re
from subprocess import Popen, PIPE
from collections import namedtuple, OrderedDict

from . import statusupdated


GET_VOL_CMD = ('amixer', 'get', 'Master')

AudioStatus = namedtuple('AudioStatus', ('volume', 'muted'))


def run_cmd(*cmd, **kwargs):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, **kwargs)
    out, err = p.communicate()
    return out.decode(), err.decode()


def get_vol():
    out, err = run_cmd(*GET_VOL_CMD)
    for line in out.splitlines():
        srch = re.search('\[([0-9]{1,3})%\]\W+?\[(on|off)\]$', line)
        if srch:
            vol, onoff = srch.groups()
            muted = True if onoff == 'off' else False
            vol = float(vol) / 100.0
            return AudioStatus(vol, muted)

icons = OrderedDict()
icons['audio-volume-muted'] = lambda aud_stat: aud_stat.muted
icons['audio-volume-low'] = lambda aud_stat: True if aud_stat.volume <= 0.3 else False
icons['audio-volume-medium'] = lambda aud_stat: True if aud_stat.volume < 0.8 else False
icons['audio-volume-high'] = lambda aud_stat: True


class VolumeImg(statusupdated.StatUpImage):
    """VolumeImg a graphical volume status widget

    It displays the volume status based on icons located in the directories
    defined in the given image loader (libqtile.images.Loader).

    Widget creation example:

    .. code-block:: python

       loader = libqtile.images.Loader(
           [
               '/usr/share/icons/Numix/32',
               '/usr/share/icons/Numix/24',
               '/usr/share/icons/Numix/22',
               '/usr/share/icons/Adwaita/32x32',
               '/usr/share/icons/Adwaita',
           ],
           width=32,
           height=32,
       )
       vol = widget.VolumeImg(loader)
       vol.status_poll_interval = 6.7 # update timeout

    Updating widget ahead of schedule by user:

    .. code-block:: python

       @libqtile.command.lazy.function
       def vol_toggle_mute(qtile):
           cmd = 'amixer sset Master toggle'
           qtile.cmd_spawn(cmd)
           qtile.call_later(
               0.1, qtile.cmd_update_status,
               'volumeimg', '', 'status_call_poller',
           )

    """

    def __init__(self, img_loader, *pargs, **kwargs):
        self.loaded_images = img_loader.icons(icons)
        if any((not x.success for x in self.loaded_images)):
            raise ValueError('Problem loading one of the volume images')
        super(VolumeImg, self).__init__(*pargs, **kwargs)

    def status_poller(self):
        audio_status = get_vol()
        for icon_name, test in icons.items():
            if test(audio_status):
                break
        return icon_name
