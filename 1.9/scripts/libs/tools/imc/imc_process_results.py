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

from scripts.libs.definitions.exit_codes import ExitCode
from typing import List
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.utils.logging import Level
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)


def is_config_error(exit_code: ExitCode) -> bool:
    """Check to see if ExitCode is in the list of Tool Config Errors

    :param exit_code: Return code from IMC
    :return: True if config error, False otherwise
    """
    if exit_code in [
        ExitCode.UNKNOWN_STATUS_CODE,
        ExitCode.FLOW_CONFIGURATION_ERROR,
        ExitCode.PARSER_NOT_SUPPORTED_ERROR,
        ExitCode.PARSER_NOT_INITIALIZED_ERROR,
        ExitCode.PARSER_COULD_NOT_INIT_ERROR,
        ExitCode.PARSER_NODE_DOES_NOT_EXIST_ERROR,
        ExitCode.XML_ZERO_GLOBAL_ITERATIONS_AND_TIME_ERROR,
        ExitCode.XML_INVALID_NODE_VALUE_ERROR,
        ExitCode.XML_INVALID_REQUESTED_VALUE_ERROR,
        ExitCode.XML_DUPLICATED_FLOW_ID_ERROR,
        ExitCode.XML_DUPLICATED_ALGORITHM_ID_ERROR,
        ExitCode.XML_INPUT_VALUE_LIMIT_REACHED_ERROR,
        ExitCode.INPUT_VALUE_LIMIT_REACHED_ERROR,
        ExitCode.TOOL_INVALID_TEST_CASE_FILE_ERROR,
        ExitCode.TOOL_CONFIGURATION_ERROR,
        ExitCode.INVALID_ARGUMENT_VALUE_ERROR,
        ExitCode.INVALID_NUMBER_OF_ARGUMENTS_ERROR,
        ExitCode.MUTUALLY_EXCLUSIVE_PARAMETERS_COMBINATION_ERROR,
    ]:
        return True  # tool failure
    return False


def is_sig_error(exit_code: ExitCode) -> bool:
    """Check to see if ExitCode is in the list of OS SIG Errors

    :param exit_code: Return code from binary instance
    :return: True if a type of sig error, False otherwise
    """
    if exit_code in [
        ExitCode.SIGTERM,
        ExitCode.SIGALRM,
        ExitCode.SIGPIPE,
        ExitCode.SIGSEGV,
        ExitCode.SIGKILL,
        ExitCode.SIGFPE,
        ExitCode.SIGABRT,
        ExitCode.SIGILL,
        ExitCode.SIGQUIT,
        ExitCode.SIGINT,
        ExitCode.SIGHUP,
    ]:
        return True
    return False


def get_execution_status(results: List) -> ExitCode:
    """Retrieves the overall execution status as well as the failure status of
    the individual processes.

    :param results: List of TestResult containing the results from the test run
    :return: ExitCode
    """
    # pylint: disable=too-many-branches
    ret_code = ExitCode.OK
    os_fail = False

    for item in results:
        test_succeeded = item.exitcode == ExitCode.OK

        # If the instance exited with an error, keep the most serious error
        # (largest positive or most negative)
        if not test_succeeded:
            # all return codes have been positive, meaning tool errors
            if not os_fail:
                # keep only if larger than current value
                if item.exitcode > ret_code:
                    ret_code = item.exitcode
                # at least one negative code has been logged, meaning OS error
                else:
                    if item.exitcode < ExitCode.OK:  # check for OS error
                        os_fail = True
                        ret_code = item.exitcode
            else:  # OS error logged
                # keep largest negative (assumes we could get multiple OS
                # errors)
                if item.exitcode < ret_code:
                    ret_code = item.exitcode

        if LoggerManagerThread.Level == Level.DEBUG:
            for line in item.stdout.split("\n"):
                if line:
                    LoggerManager().log(
                        "IMC",
                        LoggerManagerThread.Level.DEBUG,
                        f"PID-{item.pid}: {line}",
                    )

        for line in item.stderr.split("\n"):
            if line and is_config_error(item.exitcode):
                LoggerManager().log(
                    "IMC",
                    LoggerManagerThread.Level.CRITICAL,
                    f"PID-{item.pid}: {line}",
                )
            elif line:
                LoggerManager().log(
                    "IMC",
                    LoggerManagerThread.Level.ERROR,
                    f"PID-{item.pid}: {line}",
                )

        status = "PASS" if test_succeeded else "FAIL"
        exit_str = "".join(
            [
                f"PID-{item.pid}: {status}, ",
                f"exit code: {ExitCode(item.exitcode)} ({int(item.exitcode)})",
            ]
        )
        if test_succeeded:
            LoggerManager().log(
                "IMC", LoggerManagerThread.Level.DEBUG, exit_str
            )
        else:
            LoggerManager().log(
                "IMC", LoggerManagerThread.Level.ERROR, exit_str
            )

    return ExitCode(ret_code)


def process_results(results, provider_errors_encountered):
    """
    Process execution results and determine the appropriate exit code.

    Args:
        results: List of execution results
        provider_errors_encountered: Errors from the provider

    Returns:
        ExitCode: The appropriate exit code based on results analysis
    """
    # exit code section
    exit_code = ExitCode.OK

    # Report any errors to the user
    tool_ret_code = get_execution_status(results)

    # check for tool config errors
    if is_config_error(tool_ret_code):
        exit_code = ExitCode.RUNNER_TOOL_FAILED  # config failure

    # Search the error provider in the event IMC has exited successfully
    elif provider_errors_encountered:
        if tool_ret_code == ExitCode.OK:
            exit_code = ExitCode.RUNNER_OS_ERR
        elif tool_ret_code == ExitCode.FLOW_DATA_MISMATCH_ERROR:
            exit_code = ExitCode.RUNNER_OS_ERR_TOOL_CORRUPTION
        elif is_sig_error(tool_ret_code):
            exit_code = ExitCode.RUNNER_OS_ERR_TOOL_SIGBUS
        else:
            exit_code = ExitCode.RUNNER_OS_ERR_UNEXPECTED
        for err in provider_errors_encountered:
            LoggerManager().log(
                "IMC",
                LoggerManagerThread.Level.ERROR,
                f"Encountered error while testing memory: {err}",
            )
    elif tool_ret_code == ExitCode.FLOW_DATA_MISMATCH_ERROR:
        exit_code = ExitCode.RUNNER_TOOL_CORRUPTION
    elif tool_ret_code == ExitCode.OK:
        exit_code = ExitCode.OK
    else:
        exit_code = ExitCode.RUNNER_OS_ERR_UNEXPECTED

    return exit_code
