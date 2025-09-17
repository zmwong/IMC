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

import sys
from enum import IntEnum
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)


class Level(IntEnum):
    """Available logging levels."""

    OFF = 60  # No messages printed
    CRITICAL = 50  # Least messages printed
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10  # All messages above


# Initialize a global LoggerManager instance


def get_log_level_from_verbosity(verbosity: int):
    """Converts a verbosity level (0-5) to a LoggerManagerThread.Level.

    This is a central utility function to maintain consistent mapping
    between verbosity levels and logging levels across the application.

    Args:
        verbosity (int): Verbosity level, typically 0-5

    Returns:
        LoggerManagerThread.Level: The corresponding logging level
    """
    level_map = {
        0: LoggerManagerThread.Level.OFF,
        1: LoggerManagerThread.Level.CRITICAL,
        2: LoggerManagerThread.Level.ERROR,
        3: LoggerManagerThread.Level.WARNING,
        4: LoggerManagerThread.Level.INFO,
        5: LoggerManagerThread.Level.DEBUG,
    }
    return level_map.get(verbosity, LoggerManagerThread.Level.WARNING)


def init_logging(name: str, log_level=None, log_format=None):
    """Initializes the logger using the LoggerManager.

    :param name: Log name
    :param log_level: Log level and below to display - Critical errors are
        always displayed
    :param log_format: Logger specific style
    :return: Logger
    """
    LoggerManager().create_logger(name, log_level, log_format)
    return LoggerManager().manager_thread.loggers[name]["logger"]
