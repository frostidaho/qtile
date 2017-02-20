import os
import re
import subprocess

import cairocffi

from . import base
from .. import bar
from libqtile.log_utils import logger

__all__ = [
    'Volume2',
]

re_vol = re.compile('\[(\d?\d?\d?)%\]')
BUTTON_UP = 4
BUTTON_DOWN = 5
BUTTON_MUTE = 1


class Volume2(base._TextBox):
    """Widget that display and change volume

    If image_loader is set it draw widget as icons.
    """
    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("cardid", None, "Card Id"),
        ("device", "default", "Device Name"),
        ("channel", "Master", "Channel"),
        ("padding", 3, "Padding left and right. Calculated if None."),
        ("image_loader", None, "instance of libqtile.images.Loader"),
        ("update_interval", 0.2, "Update time in seconds."),
        ("emoji", False, "Use emoji to display volume states, only if ``image_loader`` is not set."
                         "The specified font needs to contain the correct unicode characters."),
        ("mute_command", None, "Mute command"),
        ("volume_up_command", None, "Volume up command"),
        ("volume_down_command", None, "Volume down command"),
        ("get_volume_command", None, "Command to get the current volume"),
    ]

    def __init__(self, **config):
        super(Volume2, self).__init__('0', width=bar.CALCULATED, **config)
        self.add_defaults(Volume2.defaults)
        if self.image_loader:
            self.length_type = bar.STATIC
            self.length = 0
        self.surfaces = {}
        self.volume = None

    def timer_setup(self):
        self.timeout_add(self.update_interval, self.update)
        if self.image_loader:
            self.setup_images()

    def create_amixer_command(self, *args):
        cmd = ['amixer']

        if (self.cardid is not None):
            cmd.extend(['-c', str(self.cardid)])

        if (self.device is not None):
            cmd.extend(['-D', str(self.device)])

        cmd.extend([x for x in args])
        return cmd

    def button_press(self, x, y, button):
        if button == BUTTON_DOWN:
            if self.volume_down_command is not None:
                subprocess.call(self.volume_down_command)
            else:
                subprocess.call(self.create_amixer_command('-q',
                                                           'sset',
                                                           self.channel,
                                                           '2%-'))
        elif button == BUTTON_UP:
            if self.volume_up_command is not None:
                subprocess.call(self.volume_up_command)
            else:
                subprocess.call(self.create_amixer_command('-q',
                                                           'sset',
                                                           self.channel,
                                                           '2%+'))
        elif button == BUTTON_MUTE:
            if self.mute_command is not None:
                subprocess.call(self.mute_command)
            else:
                subprocess.call(self.create_amixer_command('-q',
                                                           'sset',
                                                           self.channel,
                                                           'toggle'))
        self.draw()

    def update(self):
        vol = self.get_volume()
        if vol != self.volume:
            self.volume = vol
            # Update the underlying canvas size before actually attempting
            # to figure out how big it is and draw it.
            self._update_drawer()
            self.bar.draw()
        self.timeout_add(self.update_interval, self.update)

    def _update_drawer(self):
        if self.image_loader:
            self.drawer.clear(self.background or self.bar.background)
            if self.volume <= 0:
                img_name = 'audio-volume-muted'
            elif self.volume <= 30:
                img_name = 'audio-volume-low'
            elif self.volume < 80:
                img_name = 'audio-volume-medium'
            else:  # self.volume >= 80:
                img_name = 'audio-volume-high'

            self.drawer.ctx.set_source(self.surfaces[img_name])
            self.drawer.ctx.paint()
        elif self.emoji:
            if self.volume <= 0:
                self.text = u'\U0001f507'
            elif self.volume <= 30:
                self.text = u'\U0001f508'
            elif self.volume < 80:
                self.text = u'\U0001f509'
            elif self.volume >= 80:
                self.text = u'\U0001f50a'
        else:
            if self.volume == -1:
                self.text = 'M'
            else:
                self.text = '%s%%' % self.volume

    def setup_images(self):
        from libqtile.images import Loader
        ldr = self.image_loader
        images = [
            'audio-volume-high',
            'audio-volume-low',
            'audio-volume-medium',
            'audio-volume-muted',
        ]
        loaded_images = ldr.icons(*images)
        if any((x.success == False for x in loaded_images)):
            self.image_loader = None
            self.length_type = bar.CALCULATED
            logger.exception('Volume switching to text mode')
            return

        for loaded_img in loaded_images:
            img = loaded_img.surface
            img_name = loaded_img.name

            input_width = img.get_width()
            input_height = img.get_height()

            if input_width > self.length:
                self.length = int(input_width) + self.actual_padding * 2

            imgpat = cairocffi.SurfacePattern(img)

            matrix = cairocffi.Matrix()
            matrix.translate(self.actual_padding * -1, 0)

            imgpat.set_matrix(matrix)
            imgpat.set_filter(cairocffi.FILTER_BEST)
            self.surfaces[img_name] = imgpat

    def get_volume(self):
        try:
            get_volume_cmd = self.create_amixer_command('sget',
                                                        self.channel)

            if self.get_volume_command:
                get_volume_cmd = self.get_volume_command

            mixer_out = self.call_process(get_volume_cmd)
        except subprocess.CalledProcessError:
            return -1

        if '[off]' in mixer_out:
            return -1

        volgroups = re_vol.search(mixer_out)
        if volgroups:
            return int(volgroups.groups()[0])
        else:
            # this shouldn't happen
            return -1

    def draw(self):
        if self.image_loader:
            self.drawer.draw(offsetx=self.offset, width=self.length)
        else:
            super(Volume2, self).draw()

    def cmd_increase_vol(self):
        # Emulate button press.
        self.button_press(0, 0, BUTTON_UP)

    def cmd_decrease_vol(self):
        # Emulate button press.
        self.button_press(0, 0, BUTTON_DOWN)

    def cmd_mute(self):
        # Emulate button press.
        self.button_press(0, 0, BUTTON_MUTE)
