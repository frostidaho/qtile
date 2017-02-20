from .. import hook
from . import textbox

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
