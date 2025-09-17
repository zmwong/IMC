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
import os
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.components.factories.runnable_factory import RunnableFactory
from scripts.libs.system_handler import SystemHandler
from scripts.libs.utils.memory_handler import MemoryHandler
from scripts.libs.components.signal_handlers.default_handler import (
    defaultSignalHandler,
)
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
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
        exit_code = runnable.execute()
    except (ValueError, TypeError) as ex_err:
        LogManager().log("SYS", LogManagerThread.Level.ERROR, str(ex_err))
        LogManagerThread().pretty_exit("SYS", ExitCode.RUNNER_TOOL_FAILED)
        return ex_err


def summarize_test_cases(tool_args: list) -> str:
    """Create a concise summary name for the execution folder.

    Strategy:
    - Look for .xml paths or directory arguments in provided args.
    - If one XML: use its base name without extension.
    - If multiple XML: use first base name + '_multi' + count.
    - If --test_case: use 'test_case' + arg
    - If a directory path provided: use directory name.
    - Fallback: 'run'.
    - Truncate to 60 chars; append count if multi.
    """
    xmls = []
    dirs = []
    test_case = None
    for arg in tool_args:
        if arg.endswith(".xml") and os.path.exists(arg):
            xmls.append(os.path.basename(arg).replace(".xml", ""))
        elif os.path.isdir(arg):
            dirs.append(os.path.basename(os.path.abspath(arg)))
        elif arg == "--test_case":
            test_case = tool_args.index("--test_case") + 1
            if test_case < len(tool_args):
                test_case = tool_args[test_case]

    if len(xmls) == 1 and not dirs:
        base = xmls[0]
    elif len(xmls) > 1:
        base = f"{xmls[0]}_multi{len(xmls)}"
    elif dirs:
        base = dirs[0]
    elif test_case:
        base = f"test_case_{test_case}"
    else:
        base = "run"
    if len(base) > 60:
        base = base[:60]
    return base


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

    # Establish execution log folder based on test case summary BEFORE any logger is created
    summary = summarize_test_cases(argv)
    LogManager().set_execution_context(summary)
    # Register SystemHandler (creates SYS logger pointing to correct folder)
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
            LogManager().log(
                "SYS",
                LogManagerThread.Level.ERROR,
                f"Thread start error: {str(ex_err)}",
            )
            exit_code = ExitCode.RUNNER_TOOL_FAILED
            break

    for runnable_thread in runnable_threads:
        runnable_thread.join()

    LogManagerThread.pretty_exit("SYS", exit_code)
    return exit_code


if __name__ == "__main__":
    main(sys.argv[1:])
