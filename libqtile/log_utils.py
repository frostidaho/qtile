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

def _mkdir_p(path):
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
    for handler in logger.handlers:
        logger.removeHandler(handler)
    for handler in handlers:
        logger.addHandler(handler)
    logger.setLevel(log_level)
    # Capture everything from the warnings module.
    logging.captureWarnings(True)
    warnings.simplefilter("always")
    logger.warning('Starting logging for Qtile with {}'.format(logger.handlers))
    return logger

def init_log(log_level=logging.WARNING, path=DEFAULT_LOG_PATH,
             stdout=False, *other_handlers):
    """Initialize & return Qtile's root logger

    If path is given log will be written to the file at path.
    If stdout is True log will be written to stdout.

    other_handlers should behave like those found in logging.handlers
    """

    all_handlers = []
    if stdout or path:
        default_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(filename)s:%(funcName)s():L%(lineno)d %(message)s"
        )
    if stdout:
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(default_formatter)
        all_handlers.append(stream_handler)
    if path:
        _mkdir_p(os.path.dirname(path))
        file_handler = RotatingFileHandler(
            path,
            maxBytes=int(2E6),
            backupCount=5,
        )
        file_handler.setFormatter(default_formatter)
        all_handlers.append(file_handler)
    all_handlers.extend(other_handlers)
    return _init_log(log_level, *all_handlers)
