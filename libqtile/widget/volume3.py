import re
from subprocess import Popen, PIPE
from collections import namedtuple, OrderedDict

from . import statusupdated
from .. import hook


DEFAULT_UPDATE_INTERVAL = 0.5
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

class Volume3(statusupdated.StatUpImage):
    def __init__(self, img_loader, *pargs, **kwargs):
        self.loaded_images = img_loader.icons(*icons)
        if any((not x.success for x in self.loaded_images)):
            raise ValueError('Problem loading one of the volume images')
        super(Volume3, self).__init__(*pargs, **kwargs)

    def status_poller(self):
        audio_status = get_vol()
        for icon_name,test in icons.items():
            if test(audio_status):
                break
        return icon_name

