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
This module implements the definitions of an abstract system and specializes
them for usage in Windows.

The `WindowsSystem` class extends the `AbstractSystem` class and provides
Windows-specific implementations for handling processes, setting priorities,
and generating commands.
"""

import signal
import threading
import subprocess
import collections
import ctypes
from ctypes import wintypes
from scripts.libs.components.os_system.abstract_system import AbstractSystem
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


# Windows API functions for process suspend/resume
try:
    # Load libraries
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # OpenProcess and CloseHandle
    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    OpenProcess.restype = wintypes.HANDLE

    CloseHandle = kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]

    # Access rights for OpenProcess
    PROCESS_ALL_ACCESS = 0x1F0FFF

    # NT functions
    NtSuspendProcess = ntdll.NtSuspendProcess
    NtSuspendProcess.argtypes = [wintypes.HANDLE]
    NtSuspendProcess.restype = wintypes.ULONG

    NtResumeProcess = ntdll.NtResumeProcess
    NtResumeProcess.argtypes = [wintypes.HANDLE]
    NtResumeProcess.restype = wintypes.ULONG

    WINDOWS_API_AVAILABLE = True
except (AttributeError, OSError):
    # Windows APIs not available (e.g., running on non-Windows platform)
    WINDOWS_API_AVAILABLE = False


def _suspend_process(pid: int):
    """
    Suspends a Windows process using NT API.

    Args:
        pid (int): Process ID to suspend.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not WINDOWS_API_AVAILABLE:
        return False

    try:
        hProc = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not hProc:
            err = ctypes.get_last_error()
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"Failed to open process {pid}. Error: {err}",
            )
            return False

        status = NtSuspendProcess(hProc)
        CloseHandle(hProc)

        if status != 0:
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"NtSuspendProcess({pid}) returned status {status}",
            )
            return False
        else:
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"Process {pid} suspended.",
            )
            return True
    except (OSError, ctypes.WinError) as e:
        LogManager().log(
            "SYS",
            LogManagerThread.Level.DEBUG,
            f"Error suspending process {pid}: {e}",
        )
        return False


def _resume_process(pid: int):
    """
    Resumes a Windows process using NT API.

    Args:
        pid (int): Process ID to resume.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not WINDOWS_API_AVAILABLE:
        return False

    try:
        hProc = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not hProc:
            err = ctypes.get_last_error()
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"Failed to open process {pid}. Error: {err}",
            )
            return False

        status = NtResumeProcess(hProc)
        CloseHandle(hProc)

        if status != 0:
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"NtResumeProcess({pid}) returned status {status}",
            )
            return False
        else:
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"Process {pid} resumed.",
            )
            return True
    except (OSError, ctypes.WinError) as e:
        LogManager().log(
            "SYS",
            LogManagerThread.Level.DEBUG,
            f"Error resuming process {pid}: {e}",
        )
        return False


class WindowsSystem(AbstractSystem):
    """
    Windows-specific implementation of the AbstractSystem class.

    This class provides methods for handling Windows-specific functionality,
    such as safely terminating processes, setting process priorities, and
    generating commands for execution.

    Attributes:
        creation_flags (int): Flags used during process creation.
        safe_signal (int): The default signal used for safe termination.
    """

    def __init__(self) -> None:
        """
        Initializes the WindowsSystem class.

        This constructor sets the default `creation_flags` and `safe_signal`
        attributes for Windows systems.

        Example:
            ```
            windows_system = WindowsSystem()
            print(windows_system.creation_flags)
            ```
        """
        super().__init__()
        # Handle Windows-specific constants gracefully on non-Windows platforms
        try:
            self.creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            self.safe_signal = signal.CTRL_C_EVENT
        except AttributeError:
            # On non-Windows platforms, these constants don't exist
            self.creation_flags = 0
            self.safe_signal = signal.SIGINT
        self._platform = "windows"

    @property
    def platform_name(self):
        """
        Returns the platform name identifier.

        Returns:
            str: The platform name 'Windows'.
        """
        return self._platform

    @property
    def is_unix(self):
        """
        Returns whether the platform is Unix-based.

        Returns:
            bool: False as Windows is not Unix-based.
        """
        return False

    def safe_taskkill(self, thread_obj: threading.Thread):
        """
        Safely terminates a process using the Windows `taskkill` command.

        This method uses the `taskkill` command to terminate a process by its
        PID. It handles any failures quietly and returns the result of the
        `taskkill` operation.

        Args:
            thread_obj (threading.Thread): The thread object representing the
                process to terminate.

        Returns:
            collections.namedtuple: A named tuple containing the following fields:
                - taskkill_pid (int): The PID of the `taskkill` process.
                - pid (int): The PID of the process being terminated.
                - stdout (str): The standard output of the `taskkill` command.
                - stderr (str): The standard error of the `taskkill` command.
                - exitcode (int): The exit code of the `taskkill` command.

        Example:
            ```
            windows_system = WindowsSystem()
            result = windows_system.safe_taskkill(thread)
            print(result.stdout)
            ```
        """
        taskkill_cmd = "cmd /c taskkill /PID %d /T /F" % thread_obj.pid
        proc = subprocess.Popen(
            taskkill_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            encoding="utf-8",
        )  # nosec
        (stdout, stderr) = proc.communicate()
        taskkill_result = collections.namedtuple(
            "TaskkillResult", "taskkill_pid pid stdout stderr exitcode"
        )

        LogManager().log(
            "SYS",
            LogManagerThread.Level.DEBUG,
            f"Taskkill command executed for PID {thread_obj.pid}. Exit code: {proc.returncode}",
        )
        return taskkill_result(
            taskkill_pid=proc.pid,
            pid=thread_obj.pid,
            stdout=stdout,
            stderr=stderr,
            exitcode=proc.returncode,
        )

    def stop_thread(self, curr_thread):
        """
        Stops a thread using the Windows `taskkill` command.

        This method uses the [safe_taskkill](http://_vscodecontentref_/1) method to terminate a thread
        that failed to stop gracefully.

        Args:
            curr_thread (threading.Thread): The thread to stop.

        Returns:
            collections.namedtuple: The result of the `taskkill` operation.

        Example:
            ```
            windows_system = WindowsSystem()
            windows_system.stop_thread(thread)
            ```
        """
        LogManager().log(
            "SYS",
            LogManagerThread.Level.WARNING,
            f"Using TASKKILL to end {curr_thread.name} since it failed to stop when requested.",
        )
        return self.safe_taskkill(curr_thread)

    @staticmethod
    def set_priority(value: int):
        """
        Converts a priority value to a Windows-specific priority flag.

        This method maps a priority value (0-100) to a Windows priority flag
        (e.g., `/LOW`, `/NORMAL`, `/HIGH`).

        Args:
            value (int): The priority value to convert (0-100).

        Returns:
            list: A list containing the Windows priority flag.

        Example:
            ```
            priority_flag = WindowsSystem.set_priority(50)
            print(priority_flag)  # Output: ['/NORMAL']
            ```
        """
        start_priorities = [
            "/LOW",
            "/BELOWNORMAL",
            "/NORMAL",
            "/ABOVENORMAL",
            "/HIGH",
        ]
        priority_val = int(abs(value - 1) / 20)
        return [start_priorities[priority_val]]

    def generate_os_command(self, lpu: int, priority: int, command: list):
        """
        Generates a Windows-specific command for executing a tool.

        This method creates a command that sets the process priority, binds the
        process to a specific logical processing unit (LPU), and appends the
        provided command.

        Args:
            lpu (int): The logical processing unit (LPU) to bind the process to.
            priority (int): The priority value to set for the process (0-100).
            command (list): The command to execute.

        Returns:
            list: A list representing the full Windows command to execute.

        Example:
            ```
            windows_system = WindowsSystem()
            os_command = windows_system.generate_os_command(2, 50, ["python", "script.py"])
            print(os_command)
            # Output: ['cmd', '/c', 'start', '/wait', '/b', '/NORMAL', '/AFFINITY', '0x4', 'python', 'script.py', '&&', 'exit', '$LASTEXITCODE']
            ```
        """
        _cmd = [
            "cmd",
            "/c",
            "start",
            "/wait",
            "/b",
        ] + self.set_priority(priority)
        _cmd.extend(["/AFFINITY", str(hex(0x1 << lpu))])
        _cmd.extend(command)
        _cmd.extend(["&&", "exit", "$LASTEXITCODE"])
        return _cmd

    def halt_thread(self, curr_thread):
        """
        Halts a thread by suspending the associated process.

        This method uses the Windows NT API to suspend the process associated
        with the thread, effectively halting its execution.

        Args:
            curr_thread (threading.Thread): The thread to halt.
        """
        try:
            if getattr(curr_thread, "halted", False):
                return
            if hasattr(curr_thread, "proc") and curr_thread.proc:
                pid = curr_thread.proc.pid
                success = _suspend_process(pid)
                if success:
                    curr_thread.halted = True
                else:
                    LogManager().log(
                        "SYS",
                        LogManagerThread.Level.WARNING,
                        f"Failed to suspend process {pid} for thread {curr_thread.name}",
                    )
        except (AttributeError, TypeError):
            # Thread has no process or process has no PID
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"Thread {curr_thread.name} has no associated process to suspend",
            )

    def resume_thread(self, curr_thread):
        """
        Resumes a thread by resuming the associated process.

        This method uses the Windows NT API to resume the process associated
        with the thread, continuing its execution after being halted.

        Args:
            curr_thread (threading.Thread): The thread to resume.
        """
        try:
            if not getattr(curr_thread, "halted", False):
                return
            if hasattr(curr_thread, "proc") and curr_thread.proc:
                pid = curr_thread.proc.pid
                success = _resume_process(pid)
                if success:
                    curr_thread.halted = False
                else:
                    LogManager().log(
                        "SYS",
                        LogManagerThread.Level.WARNING,
                        f"Failed to resume process {pid} for thread {curr_thread.name}",
                    )
        except (AttributeError, TypeError):
            # Thread has no process or process has no PID
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"Thread {curr_thread.name} has no associated process to resume",
            )
