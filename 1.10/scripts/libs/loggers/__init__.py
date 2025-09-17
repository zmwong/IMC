#!/usr/bin/env python
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

"""
Loggers Package for Centralized Logging Management.

This package provides comprehensive logging management capabilities for the IMC tool,
including configuration, formatting, and centralized control of logging behavior
across all components. It ensures consistent logging practices and enables efficient
debugging and monitoring of the tool's operation.

The package includes:

- LoggingManager: Central logging management system that handles logger configuration,
  formatting, and coordination across different components. Provides unified logging
  interface and supports various logging levels, output formats, and destinations.

Key features:
- Centralized logging configuration and management
- Support for multiple logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Flexible output formatting and destination configuration
- Thread-safe logging operations for multi-threaded environments
- Integration with the IMC tool's error management system
- Performance-optimized logging for minimal impact on tool execution

The logging manager ensures that all components of the IMC tool can generate
consistent, well-formatted log output that aids in debugging, monitoring,
and operational analysis.
"""

from enum import IntEnum


class Level(IntEnum):
    OFF = 60
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10


def level_to_verbosity(verbosity: int) -> Level:
    """Map verbosity (0–5) to our Level enum (defaults to WARNING)."""
    level_map: dict[int, Level] = {
        0: Level.OFF,
        1: Level.CRITICAL,
        2: Level.ERROR,
        3: Level.WARNING,
        4: Level.INFO,
        5: Level.DEBUG,
    }
    return level_map.get(verbosity, Level.WARNING)
