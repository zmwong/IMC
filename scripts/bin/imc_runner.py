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
# pylint: disable=line-too-long,wrong-import-position

"""
This module is a Python wrapper intended to call tools on multiple logical processing units. 
If the target LPUs are not specified then a thread is spawned for each LPU on the system.
"""
import sys
import threading
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.components.factories.runnable_factory import RunnableFactory
from scripts.libs.system_handler import SystemHandler
from scripts.libs.utils.memory_handler import MemoryHandler
from scripts.libs.components.signal_handlers.default_handler import (
    defaultSignalHandler,
)
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)


exit_code = None


def create_runnable(tool, argv):
    """
    Creates and executes a runnable object for the specified tool.

    This function uses the `RunnableFactory` to create a runnable object for the given tool
    and its arguments. It then sets up, executes, and performs post-execution cleanup for
    the runnable. If an error occurs during setup or execution, it logs the error and exits
    with a failure code.

    Args:
        tool (str): The name of the tool to create a runnable for.
        argv (list): A list of arguments to pass to the tool.

    Raises:
        ValueError: If the tool creation or execution fails due to invalid arguments.
        TypeError: If the tool creation or execution fails due to type mismatches.
    """
    global exit_code
    runnable = RunnableFactory().create(tool, argv)
    try:
        runnable.setup()
        exit_code = runnable.execute()
    except (ValueError, TypeError) as ex_err:
        LoggerManager().log("SYS", LoggerManagerThread.Level.ERROR, str(ex_err))
        LoggerManagerThread().pretty_exit("SYS", ExitCode.RUNNER_TOOL_FAILED)
        return ex_err
    runnable.post()


def main(argv: list) -> int:
    """
    Main entry point for generating and executing runnable objects.

    This function initializes the `SystemHandler`, registers signal handlers, and creates
    threads for executing runnable objects for each tool specified in the system arguments.
    Each thread is responsible for executing a runnable object for a specific tool. The
    function waits for all threads to complete before exiting.

    Args:
        argv (list): A list of command-line arguments passed to the script.

    Returns:
        int: An exit code indicating the success or failure of the execution.

    Disclaimer:
        IntelligentMemoryChecker is the only tool supported by this script at
        the time.

    Example:
        To run the script with specific arguments:
        ```
        python runIMC.py --tool my_tool --args arg1 arg2
        ```
    """

    # Register SystemHandler
    SystemHandler(argv)
    MemoryHandler()
    # Register signal handler
    defaultSignalHandler()
    exit_code = ExitCode.OK

    runnable_threads = []
    for tool, args in SystemHandler().tools_args.items():
        if tool == "SYS":
            continue
        runnable_thread = threading.Thread(
            target=create_runnable,
            args=(
                tool,
                args,
            ),
        )
        try:
            runnable_thread.start()
            runnable_threads.append(runnable_thread)
        except Exception as ex_err:
            LoggerManager().log(
                "SYS",
                LoggerManagerThread.Level.ERROR,
                f"Thread start error: {str(ex_err)}",
            )
            exit_code = ExitCode.RUNNER_TOOL_FAILED
            break

    for runnable_thread in runnable_threads:
        runnable_thread.join()

    LoggerManagerThread().pretty_exit("SYS", exit_code)
    return exit_code


if __name__ == "__main__":
    main(sys.argv[1:])
