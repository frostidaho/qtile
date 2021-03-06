from __future__ import division
from . import base
from .. import bar


class Image2(base._Widget, base.MarginMixin):
    """Display an  image on the bar"""
    orientations = base.ORIENTATION_BOTH
    defaults = [
        ('loaded_image', None, 'image created by libqtile.images.Loader'),
    ]

    def __init__(self, length=bar.CALCULATED, **config):
        base._Widget.__init__(self, length, **config)
        self.add_defaults(Image2.defaults)
        self.add_defaults(base.MarginMixin.defaults)

        # make the default 0 instead
        self._widget_defaults["margin"] = 0

    def _configure(self, qtile, bar):
        base._Widget._configure(self, qtile, bar)
        if self.loaded_image is None:
            raise ValueError('No loaded_image given to Image2() widget.')
        if not self.loaded_image.success:
            msg = 'Image was not successfully loaded {!r}'
            raise ValueError(msg.format(self.loaded_image))

    @property
    def image(self):
        return self.loaded_image.surface

    @property
    def pattern(self):
        return self.loaded_image.pattern

    @property
    def image_width(self):
        return self.loaded_image.width

    @property
    def image_height(self):
        return self.loaded_image.height

    def draw(self):
        self.drawer.clear(self.bar.background)
        self.drawer.ctx.save()
        self.drawer.ctx.translate(self.margin_x, self.margin_y)
        self.drawer.ctx.set_source(self.pattern)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()

        if self.bar.horizontal:
            self.drawer.draw(offsetx=self.offset, width=self.width)
        else:
            self.drawer.draw(offsety=self.offset, height=self.width)

    def calculate_length(self):
        if self.bar.horizontal:
            return self.image_width + (self.margin_x * 2)
        else:
            return self.image_height + (self.margin_y * 2)
