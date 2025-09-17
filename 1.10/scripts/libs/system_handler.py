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
# pylint: disable=line-too-long

"""
This module implements a singleton class that handles the information of the whole
system. It is responsible for parsing command-line arguments, setting up the system
logger, and managing the operating system environment.
"""

import sys
import argparse
from scripts.libs.utils.logging import get_log_level_from_verbosity
import platform
import os
import scripts.libs.utils.arg_support as argspt
from scripts.libs.utils.singleton_meta import SingletonMeta
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


def parse_arguments(args, default_key="IMC"):
    """
    Parses command-line arguments and organizes them into a dictionary.

    This function supports multiple tool flags and assigns arguments to their
    respective tools. If no tool flag is present, all arguments are assigned
    to the default key.

    Args:
        args (list): List of command-line arguments.
        default_key (str): The default key to assign arguments if no tool flag is present.

    Returns:
        dict: A dictionary where keys are tool names and values are lists of arguments.

    Example:
        ```
        args = ["--IMC", "-v", "--SYS", "--version"]
        parsed_args = parse_arguments(args)
        print(parsed_args)
        # Output: {'IMC': ['-v'], 'SYS': ['--version']}
        ```
    """
    supported_tool_flags = ["--IMC", "--SYS"]

    arguments = {}
    default_arguments = []

    tool_flag_present = any(arg in supported_tool_flags for arg in args)

    if not tool_flag_present:
        arguments[default_key] = args
        return arguments

    current_tool = None
    i = 0
    while i < len(args):
        if args[i] in supported_tool_flags:
            key = args[i][2:]
            arguments[key] = []
            current_tool = key
        else:
            arguments[current_tool].append(args[i])
        i += 1

    if default_arguments:
        arguments[default_key] = " ".join(default_arguments)

    return arguments


class SystemHandler(metaclass=SingletonMeta):
    """
    Singleton class that handles system-level information and operations.

    The `SystemHandler` class is responsible for parsing command-line arguments,
    setting up the system logger, and managing the operating system environment.

    Attributes:
        os_system (object): The operating system abstraction for managing system-specific operations.
        tools_args (dict): Parsed command-line arguments organized by tool.
        args (argparse.Namespace): Parsed system-specific arguments.
        LOGGER (logging.Logger): The logger instance for system-level logging.
    """

    def define_sys_parser(self):
        """
        Defines the command-line argument parser for system-level operations.

        This method sets up the argument parser with various options and flags
        specific to system-level operations. It is used to parse command-line
        arguments when the script is executed.

        Example:
            ```
            parser = SystemHandler().define_sys_parser()
            args = parser.parse_args()
            ```
        """
        parser = argparse.ArgumentParser(
            description="Parse system-level arguments.",
            epilog="Example: runIMC.py --SYS -v",
            formatter_class=argparse.RawTextHelpFormatter,
        )

        parser.add_argument(
            "-V",
            "--version",
            action="version",
            version=str(0.2),
            help="Show the version of the system",
        )

        parser.add_argument(
            "-v",
            dest="verbosity",
            default=4,
            action=argspt.VerboseAction,
            help="Sets available verbosity level. -v off turns off all output to "
            + "the screen. Default is -vvvv.",
        )
        self.parser = parser

    def __init__(self, argv=None) -> None:
        """
        Initializes the SystemHandler class.

        This constructor sets up the operating system environment, parses command-line
        arguments, sets up the system logger, and loads the appropriate OS-specific
        system handler. It ensures that the script is running on Python 3.7 or newer.

        Args:
            argv (list, optional): List of command-line arguments. Defaults to `sys.argv`.

        Raises:
            RuntimeError: If the Python version is older than 3.7.

        Example:
            ```
            handler = SystemHandler(sys.argv)
            print(handler.os_system.platform_name)  # Outputs the OS name
            ```
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True

            # Ensure Python version compatibility
            REQ_VER = (3, 7)
            if not sys.version_info[0:2] >= REQ_VER:
                raise RuntimeError(
                    f"This module requires Python "
                    + f"{'.'.join([str(v) for v in REQ_VER])} or newer."
                )
            # Setup system arguments
            self.args = self.define_sys_parser()
            # Set up the operating system environment
            self.init_os_system()

            # Parse command-line arguments
            self.tools_args = parse_arguments(argv or sys.argv[1:])
            self.args = argparse.Namespace(**self.tools_args)
            self.system_args = self.parser.parse_args(
                self.tools_args.get("SYS", [])
            )

        self.logger_name = "SYS"
        verbosity = self._get_verbosity_from_args()
        log_level = self._get_log_level_from_verbosity(verbosity)

        # Initialize the SYS logger
        LogManager().create_logger(
            name=self.logger_name, log_level=log_level, log_format=None
        )

        self.verbosity = verbosity
        self.logger_level = log_level

        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.DEBUG,
            f"Command line: {' '.join(sys.argv)}",
        )

    def _get_verbosity_from_args(self):
        """
        Extracts the verbosity level from command line arguments.

        Returns:
            int: The verbosity level (0-5), with a default of 4.
        """
        verbosity = 4

        args_to_check = []
        if "IMC" in self.tools_args:
            args_to_check.extend(self.tools_args["IMC"])

        for i, arg in enumerate(args_to_check):
            if arg == "-v" and i + 1 < len(args_to_check):
                if args_to_check[i + 1].lower() == "off":
                    return 0
                try:
                    return int(args_to_check[i + 1])
                except ValueError:
                    pass
            elif arg.startswith("-") and all(c == "v" for c in arg[1:]):
                return len(arg) - 1

        return verbosity

    def _get_log_level_from_verbosity(self, verbosity):
        """
        Maps a verbosity level to a LogManagerThread.Level.

        Args:
            verbosity (int): The verbosity level (0-5)

        Returns:
            LogManagerThread.Level: The corresponding logging level
        """
        return get_log_level_from_verbosity(verbosity)

    def get_verbosity(self):
        """
        Returns the current verbosity level.

        This method allows other components to access the system verbosity level.

        Returns:
            int: The current verbosity level (0-5)
        """
        return getattr(self, "verbosity", 4)

    def init_os_system(self):
        system = platform.system().lower()
        if system == "linux":
            # Check if SVOS
            if os.path.exists("/etc/svos"):
                system = "svos"
        if system not in ["windows", "linux", "svos"]:
            raise RuntimeError(
                f"Unsupported operating system: {system}. Supported OS are: "
                + "Windows, Linux, SVOS."
            )
        else:
            if system == "windows":
                from scripts.libs.components.os_system.windows import (
                    WindowsSystem,
                )

                self.os_system = WindowsSystem()
            elif system == "linux":
                from scripts.libs.components.os_system.linux import LinuxSystem

                self.os_system = LinuxSystem()
            elif system == "svos":
                from scripts.libs.components.os_system.svos import SvosSystem

                self.os_system = SvosSystem()
