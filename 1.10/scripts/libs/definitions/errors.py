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
# pylint: disable=invalid-name,too-few-public-methods,missing-class-docstring

"""This module contains the definitions used in the error provider factory."""

import enum


class ErrorType(enum.Enum):
    """Error type enum class."""

    Unknown = -1
    Correctable = 0
    CE = 0  # Duplicate for Correctable error so we can get it's string name
    Uncorrectable = 1
    UE = 1  # Duplicate for Uncorrectable error so we can get it's string name

    def __str__(self):
        return self.name


class ErrorProvider(enum.Enum):
    """Error provider name enum class."""

    Auto = -1
    NoProvider = 0
    EDAC = 1
    EDACFS = 2
    Ftrace = 3

    def __str__(self):
        return self.name


class ErrorEntry:
    """Error entry base class"""

    def __init__(self):
        self.raw = None

        self.socket = None
        self.mc = None
        self.channel = None
        self.slot = None

        self.error_type = ErrorType.Unknown
        self.count = 0


class ErrorProviderNotFound(Exception):
    pass


class ErrorProviderNotSet(Exception):
    pass


PROVIDER_NAMES = {
    "auto": ErrorProvider.Auto,
    "none": ErrorProvider.NoProvider,
    "edac": ErrorProvider.EDAC,
    "edacfs": ErrorProvider.EDACFS,
    "ftrace": ErrorProvider.Ftrace,
}


class XMLGeneratorStatus(enum.Enum):
    OK = 0, "OK"

    REQUIRED_VALUE_NOT_FOUND = 300, "The provided required value doesnt exist."
    VALUE_NOT_FOUND = 301, "The provided value doesnt exist."
    INVALID_REQUIRED_VALUE = (
        302,
        "The provided type for the required field is not valid.",
    )
    INVALID_VALUE = 303, "Non-required value is not valid."
    INCOMPATIBLE_CONFIGURATION = (
        304,
        "The provided configuration is not compatible.",
    )
    REQUIRED_IDENTIFIER_DOES_NOT_EXIST = (
        305,
        "The identifier for the required parameter is not defined.",
    )
    REQUIRED_VALUE_NOT_DEFINED = 306, "Required value is not defined."
    VALUE_NOT_DEFINED = 307, "Value is not defined."

    INVALID_PATH = 308, "The provided path doesnt exist or its not accessible."

    def __int__(self):
        return int(self.value)

    def __lt__(self, other):
        if isinstance(other, (int, XMLGeneratorStatus)):
            return int(self.value) < int(other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, (int, XMLGeneratorStatus)):
            return int(self.value) > int(other)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, (int, XMLGeneratorStatus)):
            return int(self.value) == int(other)
        return NotImplemented

    def __str__(self):
        return self.description

    @enum.DynamicClassAttribute
    def value(self):
        """
        Overrides the enum value method.  Gets the value of the Enum member.
        """
        if isinstance(self._value_, tuple):
            return self._value_[0]
        return self._value_

    @property
    def description(self):
        """Gets the description of the ExitCode enum."""
        if isinstance(self._value_, tuple):
            return self._value_[1]
        return "No description available."
