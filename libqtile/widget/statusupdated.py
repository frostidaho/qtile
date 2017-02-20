from .. import hook, configurable, bar
from . import textbox, base

class _StatusUpdatedMixin(object):

    def _configure(self, qtile, bar):
        super(_StatusUpdatedMixin, self)._configure(qtile, bar)

        @hook.subscribe.status_update(self.status_name)
        def on_update(status, *pargs, **kwargs):
            self.status = status
            self.status_update()

    @property
    def status_name(self):
        try:
            return self._status_name
        except AttributeError:
            sn = self.__class__.__name__.lower()
            self.status_name = sn
            return sn

    @status_name.setter
    def status_name(self, value):
        self._status_name = value

    @property
    def status(self):
        try:
            return self._status
        except AttributeError:
            self.status = None
            return self.status

    @status.setter
    def status(self, value):
        self._status = value


class StatUpText(_StatusUpdatedMixin, textbox.TextBox):
    def status_update(self):
        super(StatUpText, self).update(self.status)

    @property
    def status(self):
        try:
            return self._status
        except AttributeError:
            self.status = self.text
            return self.status

    @status.setter
    def status(self, value):
        self._status = value


class StatUpImage(_StatusUpdatedMixin, base._Widget):
    """Display an image on the bar"""
    orientations = base.ORIENTATION_BOTH
    defaults = [
        ('loaded_images', None, 'images created by libqtile.images.Loader'),
        ("margin", 0, "Margin inside the box"),
        ("margin_x", None, "X Margin. Overrides 'margin' if set"),
        ("margin_y", None, "Y Margin. Overrides 'margin' if set"),
    ]
    margin_x = configurable.ExtraFallback('margin_x', 'margin')
    margin_y = configurable.ExtraFallback('margin_y', 'margin')

    def __init__(self, length=bar.CALCULATED, **config):
        super(StatUpImage, self).__init__(length=bar.CALCULATED, **config)
        self.add_defaults(StatUpImage.defaults)

    def _configure(self, qtile, bar):
        super(StatUpImage, self)._configure(qtile, bar)
        self.set_image(self.status)

    def set_image(self, name_or_path):
        imgs = self.loaded_images
        for img in imgs:
            if img.name == name_or_path:
                break
            elif img.path == name_or_path:
                break
        else:
            img = imgs[0]
        if not img.success:
            raise ValueError('Image was not successfully loaded {!r}'.format(img))
        self.image = img.surface
        self.pattern = img.pattern

    def status_update(self):
        self.set_image(self.status)
        self.draw()

    @property
    def image_width(self):
        return self.image.get_width()

    @property
    def image_height(self):
        return self.image.get_height()

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
