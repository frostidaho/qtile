# Copyright (c) 2012 Florian Mounier
# Copyright (c) 2013-2014 Tao Sauvage
# Copyright (c) 2014 Sean Vig
# Copyright (c) 2014 roger
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import warnings
import errno

logger = logging.getLogger(__package__)
LOG_DIR = os.path.expanduser(os.path.join(
    os.getenv('XDG_DATA_HOME', '~/.local/share'),
    'qtile',
))
DEFAULT_LOG_PATH = os.path.join(LOG_DIR, 'qtile.log')
TESTS_LOG_PATH = os.path.join(LOG_DIR, 'tests_qtile.log')


def init_log(log_level=logging.WARNING, path=DEFAULT_LOG_PATH,
             stream_handler=False, *other_handlers):
    """Initialize & return Qtile's root logger

    If path is given log will be written to the file at path.
    If stream_handler is True log will be written to stdout.

    other_handlers should behave like those found in logging.handlers
    """
    def mkdir_p(path):
        """Create directory at path. Does not raise exception if it already exists.

        Found at: http://stackoverflow.com/a/600612
        """
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def _init_log(log_level, *handlers):
        "Set logger to log_level & add handlers"
        if not logger.hasHandlers():
            for handler in handlers:
                logger.addHandler(handler)
        logger.setLevel(log_level)
        # Capture everything from the warnings module.
        logging.captureWarnings(True)
        warnings.simplefilter("always")
        # msg = 'Starting logging for Qtile with {} handlers'
        # logger.warning(msg.format(len(logger.handlers)))
        logger.warning('Starting logging for Qtile with {}'.format(logger.handlers))
        return logger

    all_handlers = []
    if stream_handler or path:
        default_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(filename)s:%(funcName)s():L%(lineno)d %(message)s"
        )
    if stream_handler:
        shandler = logging.StreamHandler(stream=sys.stdout)
        shandler.setFormatter(default_formatter)
        all_handlers.append(shandler)
    if path:
        mkdir_p(os.path.dirname(path))
        file_handler = RotatingFileHandler(
            path,
            maxBytes=int(2E6),
            backupCount=5,
        )
        file_handler.setFormatter(default_formatter)
        all_handlers.append(file_handler)
    all_handlers.extend(other_handlers)
    return _init_log(log_level, *all_handlers)
