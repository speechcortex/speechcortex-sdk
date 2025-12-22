# Copyright 2024 Zeus SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Custom log levels for Python's :mod:`logging` module.

The :mod:`verboselogs` module defines the :data:`NOTICE`, :data:`SPAM`,
:data:`SUCCESS` and :data:`VERBOSE` constants, the :class:`VerboseLogger` class
and the :func:`add_log_level()` and :func:`install()` functions.
"""

import logging

__version__ = "1.8"

NOTICE = 25
SPAM = 5
SUCCESS = 35
VERBOSE = 15

WARNING = logging.WARNING
ERROR = logging.ERROR
FATAL = logging.FATAL
CRITICAL = logging.CRITICAL
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET


def install():
    """
    Make :class:`VerboseLogger` the default logger class.
    """
    logging.setLoggerClass(VerboseLogger)


def add_log_level(value, name):
    """
    Add a new log level to the :mod:`logging` module.

    :param value: The log level's number (an integer).
    :param name: The name for the log level (a string).
    """
    logging.addLevelName(value, name)
    setattr(logging, name, value)


# Define custom log levels
add_log_level(NOTICE, "NOTICE")
add_log_level(SPAM, "SPAM")
add_log_level(SUCCESS, "SUCCESS")
add_log_level(VERBOSE, "VERBOSE")


class VerboseLogger(logging.Logger):
    """
    Custom logger class to support additional logging levels.
    """

    def __init__(self, *args, **kw):
        logging.Logger.__init__(self, *args, **kw)
        self.parent = logging.getLogger()

    def notice(self, msg, *args, **kw):
        """Log a message with level NOTICE."""
        if self.isEnabledFor(NOTICE):
            self._log(NOTICE, msg, args, **kw)

    def spam(self, msg, *args, **kw):
        """Log a message with level SPAM."""
        if self.isEnabledFor(SPAM):
            self._log(SPAM, msg, args, **kw)

    def success(self, msg, *args, **kw):
        """Log a message with level SUCCESS."""
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kw)

    def verbose(self, msg, *args, **kw):
        """Log a message with level VERBOSE."""
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kw)
