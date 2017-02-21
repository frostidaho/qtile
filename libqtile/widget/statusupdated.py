import sys
import traceback
from .. import hook, configurable, bar, log_utils
from . import textbox, base

logger = log_utils.logger
DEFAULT_UPDATE_INTERVAL = 1.0

class _StatusUpdatedMixin(object):
    """_StatusUpdatedMixin

    Classes which inherit from _StatusUpdatedMixin should define
    cls.status_update() - which will refresh the widget with current status

    Optional:
    cls.status_poller() - a method for widgets that need polling
                          it returns a new status
    cls.status_poll_timeout - timeout for status_poller in seconds
    """

    def _configure(self, qtile, bar):
        super(_StatusUpdatedMixin, self)._configure(qtile, bar)

        @hook.subscribe.status_update(self.status_name)
        def on_update(status, *pargs, **kwargs):
            self.status_set_and_update(status, *pargs, **kwargs)

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

    @property
    def status_poll_timeout(self):
        try:
            return self._status_poll_timeout
        except AttributeError:
            self.status_poll_timeout = DEFAULT_UPDATE_INTERVAL
            return self.status_poll_timeout

    @status_poll_timeout.setter
    def status_poll_timeout(self, value):
        self._status_poll_timeout = value

    def status_set_and_update(self, status, method_name='', *pargs, **kwargs):
        "Set status & run status_update()"
        if method_name:
            logger.info('%r is running %r', self, method_name)
            return getattr(self, method_name)()

        self.status = status
        try:
            self.status_update(*pargs, **kwargs)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            logger.warning('status_update failed: {}'.format(' '.join(lines)))

    def status_call_poller(self):
        def callback(future):
            try:
                result = future.result()
            except Exception:
                logger.exception('status_poller() raised an exception in status_call_poller.callback')
                return
            self.status_set_and_update(result)

        try:
            future = self.qtile.run_in_executor(self.status_poller)
            future.add_done_callback(callback)
        except Exception:
            logger.exception('status_poller() raised an exception in status_call_poller')

    def timer_setup(self):
        def callback(future):
            try:
                result = future.result()
            except Exception:
                logger.exception(
                    ('status_poller() raised an exception in '
                     'timer_setup.callback. Not rescheduling status_poller()'))
                return
            self.status_set_and_update(result)
            self.timeout_add(self.status_poll_timeout, fn)

        def fn():
            future = self.qtile.run_in_executor(self.status_poller)
            future.add_done_callback(callback)
            return future

        try:
            self.status_poller
            fn()
            logger.info('Set up status_poller for %r', self)
        except AttributeError:
            logger.info('No status_poller for %r', self)

        try:
            super(_StatusUpdatedMixin, self).timer_setup()
        except AttributeError:
            logger.info("Widget class %r does not have a timer_setup on superclass")


class StatUpText(_StatusUpdatedMixin, textbox.TextBox):
    def status_update(self, *pargs, **kwargs):
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

    def status_update(self, *pargs, **kwargs):
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
