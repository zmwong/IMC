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

"""
This module implements the definitions of an abstract OS and specializes 
them for usage in Linux systems.

It provides Linux-specific implementations of methods for setting process
priorities, generating OS-specific commands, and stopping threads.
"""

import os
import signal
from scripts.libs.components.os_system.abstract_system import AbstractSystem
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)


class LinuxSystem(AbstractSystem):
    """
    Linux-specific implementation of the AbstractSystem class.

    This class provides methods for handling Linux-specific functionality,
    such as setting process priorities, generating commands, and stopping threads.

    Attributes:
        creation_flags (int): Flags used during process creation.
        safe_signal (int): The default signal used for safe termination.
    """

    def __init__(self) -> None:
        """
        Initializes the LinuxSystem class.

        Sets default values for `creation_flags` and `safe_signal`.
        """
        super().__init__()
        self.creation_flags = 0
        self.safe_signal = signal.SIGINT
        self._platform = "linux"

    @property
    def platform_name(self):
        """
        Returns the platform name identifier.

        Returns:
            str: The platform name 'linux'.
        """
        return self._platform

    @property
    def is_unix(self):
        """
        Returns whether the platform is Unix-based.

        Returns:
            bool: True as Linux is Unix-based.
        """
        return True

    def set_priority(self, value: int):
        """
        Converts a priority value to a 'nice' value.

        This method converts a given priority value (0-100) to a Linux 'nice' value
        (-20 to 19). If the process is not running as root and the calculated 'nice'
        value is negative, it defaults to 0.

        Args:
            value (int): The priority value to convert (0-100).

        Returns:
            list: A list containing the command to set the priority and the resulting
            'nice' value.

        Example:
            ```
            linux_system = LinuxSystem()
            priority_command = linux_system.set_priority(50)
            print(priority_command)  # Output: ['nice', '-n', '0']
            ```
        """
        nice_val = round(
            ((value) / 100) * -39 + 19
        )  # Convert it to a 'nice' value
        if os.geteuid() != 0 and nice_val < 0:
            nice_val = 0
        return ["nice", "-n", str(nice_val)]

    def generate_os_command(self, lpu: int, priority: int, command: list):
        """
        Generates a Linux-specific command for executing a tool.

        This method creates a command that sets the process priority, binds the
        process to a specific logical processing unit (LPU), and appends the
        provided command.

        Args:
            lpu (int): The logical processing unit (LPU) to bind the process to.
            priority (int): The priority value to set for the process (0-100).
            command (list): The command to execute.

        Returns:
            list: A list representing the full Linux command to execute.

        Example:
            ```
            linux_system = LinuxSystem()
            os_command = linux_system.generate_os_command(2, 50, ["python", "script.py"])
            print(os_command)
            # Output: ['nice', '-n', '0', 'taskset', '-c', '2', 'python', 'script.py']
            ```
        """
        _cmd = self.set_priority(priority) + [
            "taskset",
            "-c",
            str(lpu),
        ]
        _cmd.extend(command)
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.DEBUG,
            f"Generated OS command: {' '.join(_cmd)}",
        )

        return _cmd

    def stop_thread(self, curr_thread):
        """
        Stops a thread by sending a SIGKILL signal.

        This method sends a SIGKILL signal to the specified thread to forcefully
        terminate it. If the thread fails to stop gracefully, a debug message is logged.

        Args:
            curr_thread (threading.Thread): The thread to stop.

        Returns:
            None

        Example:
            ```
            linux_system = LinuxSystem()
            linux_system.stop_thread(thread)
            ```
        """
        self.safe_kill(curr_thread, signal.SIGKILL)
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.DEBUG,
            f"Sending SIGKILL to {curr_thread.name} since it failed to stop when requested.",
        )
        return None
