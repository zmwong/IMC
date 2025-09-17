#!/usr/bin/python
# /****************************************************************************
# INTEL CONFIDENTIAL
# Copyright 2017-2025 Intel Corporation.
# This software and the related documents are Intel copyrighted materials,
# and your use of them is governed by the express license under which they
# were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit
# this software or the related documents without Intel's prior written
# permission. This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly
# stated in the License.
# -NDA Required
# ****************************************************************************/
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long,expression-not-assigned

"""This is a helper module to initialize and support logging functionally."""

from enum import IntEnum
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


class Level(IntEnum):
    """Available logging levels."""

    OFF = 60  # No messages printed
    CRITICAL = 50  # Least messages printed
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10  # All messages above


# Initialize a global LogManager instance


def get_log_level_from_verbosity(verbosity: int):
    """Converts a verbosity level (0-5) to a LogManagerThread.Level.

    This is a central utility function to maintain consistent mapping
    between verbosity levels and logging levels across the application.

    Args:
        verbosity (int): Verbosity level, typically 0-5

    Returns:
        LogManagerThread.Level: The corresponding logging level
    """
    level_map = {
        0: LogManagerThread.Level.OFF,
        1: LogManagerThread.Level.CRITICAL,
        2: LogManagerThread.Level.ERROR,
        3: LogManagerThread.Level.WARNING,
        4: LogManagerThread.Level.INFO,
        5: LogManagerThread.Level.DEBUG,
    }
    return level_map.get(verbosity, LogManagerThread.Level.WARNING)


def init_logging(name: str, log_level=None, log_format=None):
    """Initializes the logger using the LogManager.

    :param name: Log name
    :param log_level: Log level and below to display - Critical errors are
        always displayed
    :param log_format: Logger specific style
    :return: Logger
    """
    LogManager().create_logger(name, log_level, log_format)
    return LogManager().manager_thread.loggers[name]["logger"]
