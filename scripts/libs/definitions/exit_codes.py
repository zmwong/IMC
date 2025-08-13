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
# pylint: disable=line-too-long
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long,expression-not-assigned

"""Definitions of values used for the orchestration script and its libraries."""

import enum


class ExitCode(enum.Enum):
    """
    This is an enum based class with custom overrides.
    It is used to handle Intelligent Memory Checker completion status and
    provide completion codes for the orchestration script.
    """

    # pylint: disable=no-member
    # Be sure to add a description to the enum values
    RUNNER_TOOL_FAILED = (
        254,
        "Intelligent Memory Checker configuration or internal error",
    )
    RUNNER_OS_ERR = 244, "".join(
        [
            "Intelligent Memory Checker found no failures but the OS or ",
            "error provider found a failure",
        ]
    )
    RUNNER_OS_ERR_TOOL_SIGBUS = 243, "".join(
        [
            "One or more Intelligent Memory Checker ",
            "instances failed unexpectedly, and the OS has detected one or more ",
            "uncorrectable HW errors",
        ]
    )
    RUNNER_OS_ERR_TOOL_CORRUPTION = 242, "".join(
        [
            "One or more Intelligent Memory Checker instances detected ",
            "one or more memory check miscompares, and the OS has detected one ",
            "or more correctable or uncorrectable HW errors",
        ]
    )
    RUNNER_TOOL_CORRUPTION = 241, "".join(
        [
            "One or more IMC tool instances detected ",
            "one or more memory check miscompares",
        ]
    )
    RUNNER_OS_ERR_UNEXPECTED = 235, "".join(
        [
            "There is a combination of HW errorstatus that cannot be ",
            "reconciled with an IMC tool instance status (i.e., only correctable ",
            "errors detected, and there was a tool SIGBUS indication or crash",
        ]
    )

    SIGTERM = -15, "SIGTERM - Termination signal"
    SIGALRM = -14, "SIGALRM - Timer signal from alarm(2)"
    SIGPIPE = -13, "SIGPIPE - Broken pipe: write to pipe with no readers"
    SIGSEGV = -11, "SIGSEGV - Invalid memory reference"
    SIGKILL = -9, "SIGKILL - Kill signal"
    SIGFPE = -8, "SIGFPE - Floating point exception"
    SIGABRT = -6, "SIGABRT - Abort signal from abort(3)"
    SIGILL = -4, "SIGILL - Illegal Instruction"
    SIGQUIT = -3, "SIGQUIT - Quit from keyboard"
    SIGINT = -2, "SIGINT - Interrupt from keyboard"
    SIGHUP = -1, "".join(
        [
            "SIGHUP - Hangup detected on controlling terminal ",
            "or death of controlling process",
        ]
    )

    OK = 0, "OK"

    # binary completion codes
    FLOW_DATA_MISMATCH_ERROR = 1, "FLOW_DATA_MISMATCH_ERROR"
    FLOW_CONFIGURATION_ERROR = 2, "FLOW_CONFIGURATION_ERROR"
    PARSER_NOT_SUPPORTED_ERROR = 3, "PARSER_NOT_SUPPORTED_ERROR"
    PARSER_NOT_INITIALIZED_ERROR = 4, "PARSER_NOT_INITIALIZED_ERROR"
    PARSER_COULD_NOT_INIT_ERROR = 5, "PARSER_COULD_NOT_INIT_ERROR"
    PARSER_NODE_DOES_NOT_EXIST_ERROR = 6, "PARSER_NODE_DOES_NOT_EXIST_ERROR"
    XML_ZERO_GLOBAL_ITERATIONS_AND_TIME_ERROR = (
        7,
        "XML_ZERO_GLOBAL_ITERATIONS_AND_TIME_ERROR",
    )
    XML_INVALID_NODE_VALUE_ERROR = 8, "XML_INVALID_NODE_VALUE_ERROR"
    # LOD (imc_internal)
    XML_NODE_DOES_NOT_EXIST_ERROR = 9, "XML_NODE_DOES_NOT_EXIST_ERROR"
    XML_INVALID_REQUESTED_VALUE_ERROR = 10, "XML_INVALID_REQUESTED_VALUE_ERROR"
    XML_DUPLICATED_FLOW_ID_ERROR = 11, "XML_DUPLICATED_FLOW_ID_ERROR"
    XML_DUPLICATED_ALGORITHM_ID_ERROR = 12, "XML_DUPLICATED_ALGORITHM_ID_ERROR"
    XML_INPUT_VALUE_LIMIT_REACHED_ERROR = (
        13,
        "XML_INPUT_VALUE_LIMIT_REACHED_ERROR",
    )
    INPUT_VALUE_LIMIT_REACHED_ERROR = 14, "INPUT_VALUE_LIMIT_REACHED_ERROR"
    # LOD (imc_internal)
    FACTORY_NOT_SUPPORTED_ERROR = 15, "FACTORY_NOT_SUPPORTED_ERROR"
    # LOD (imc_internal)
    FACTORY_NOT_INITIALIZED_ERROR = 16, "FACTORY_NOT_INITIALIZED_ERROR"
    # LOD (imc_internal)
    FACTORY_COULD_NOT_INIT_ERROR = 17, "FACTORY_COULD_NOT_INIT_ERROR"
    # LOD (imc_internal)
    FACTORY_NODE_DOES_NOT_EXIST_ERROR = 18, "FACTORY_NODE_DOES_NOT_EXIST_ERROR"
    FACTORY_LIMIT_REACHED_ERROR = 19, "FACTORY_LIMIT_REACHED_ERROR"
    # LOD (imc_internal)
    FACTORY_OPCODE_FIND_NOT_SUPPORTED_ERROR = (
        20,
        "FACTORY_OPCODE_FIND_NOT_SUPPORTED_ERROR",
    )
    # LOD (imc_internal)
    FACTORY_OBJECT_REQUIRE_FREE = 21, "FACTORY_OBJECT_REQUIRE_FREE"
    MEMORY_ALLOCATOR_LIMIT_REACHED_ERROR = (
        22,
        "MEMORY_ALLOCATOR_LIMIT_REACHED_ERROR",
    )
    # LOD (imc_internal)
    MEMORY_ALLOCATOR_MEMORY_BLOCKS_ALREADY_TRANSFORMED_ERROR = (
        23,
        "MEMORY_ALLOCATOR_MEMORY_BLOCKS_ALREADY_TRANSFORMED_ERROR",
    )
    # LOD (imc_internal)
    MEMORY_ALLOCATOR_CANNOT_CREATE_MEMORY_BLOCK_ERROR = (
        24,
        "MEMORY_ALLOCATOR_CANNOT_CREATE_MEMORY_BLOCK_ERROR",
    )
    # LOD (imc_internal)
    FREE_MEMORY_HANDLER_ONLY_ONE_ALLOWED_ERROR = (
        25,
        "FREE_MEMORY_HANDLER_ONLY_ONE_ALLOWED_ERROR",
    )
    TOOL_INVALID_TEST_CASE_FILE_ERROR = 26, "TOOL_INVALID_TEST_CASE_FILE_ERROR"
    TOOL_CONFIGURATION_ERROR = 27, "TOOL_CONFIGURATION_ERROR"
    # LOD (imc_internal)
    NOT_AN_INTEL_PLATFORM_ERROR = 28, "A Non-Intel platform was detected"
    INVALID_ARGUMENT_VALUE_ERROR = (
        29,
        "A command line argument has an invalid value",
    )
    INVALID_NUMBER_OF_ARGUMENTS_ERROR = 30, "The number of arguments is invalid"
    MUTUALLY_EXCLUSIVE_PARAMETERS_COMBINATION_ERROR = (
        31,
        "An invalid combination of parameters (mutually exclusion)",
    )
    TOOL_ENDED_USING_TASKKILL = 32, "".join(
        [
            "Taskkill has been used to end the thread, no return code is ",
            "received from IMC",
        ]
    )
    UNKNOWN_STATUS_CODE = 255, "An unknown error occurred"

    def __int__(self):
        return int(self.value)

    def __lt__(self, other):
        if isinstance(other, (int, ExitCode)):
            return int(self.value) < int(other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, (int, ExitCode)):
            return int(self.value) > int(other)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, (int, ExitCode)):
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

    @classmethod
    def _missing_(cls, value):
        # override enums _missing_ to handle the tuple/exception
        # Since we're packing the enum with a tuple we might end up here when
        # running ExitCode(Num)
        for member in cls.__members__.values():
            if value in (member.value, member.name):
                return member
        # Otherwise return a generic error
        return cls.UNKNOWN_STATUS_CODE
