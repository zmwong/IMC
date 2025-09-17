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
This module provides the base implementation of what an OS system should implement.

It defines an abstract base class (`AbstractSystem`) that provides a common interface
for system-specific implementations. This includes methods for safely killing threads,
checking CPU instruction sets, setting process priorities, generating OS-specific
commands, and stopping threads.
"""

from abc import ABC, abstractmethod
import os
import signal
import threading
from scripts.libs.utils.cpu_id import CPUID


class AbstractSystem(ABC):
    """
    Abstract base class for system-specific implementations.

    This class provides a common interface for different operating systems to implement
    system-specific functionality, such as handling signals, setting process priorities,
    and generating OS-specific commands.

    Methods:
        safe_kill(thread_obj, sig_type): Safely kills a thread or process.
        get_highest_cpu_instruction_set(): Returns the highest CPU instruction set available.
        set_priority(value): Converts a priority value to a 'nice' value (abstract).
        generate_os_command(test_case, mem_per_instance, lpu): Generates an OS-specific command (abstract).
        stop_thread(curr_thread): Stops a thread in an OS-specific way (abstract).
    """

    @property
    @abstractmethod
    def platform_name(self):
        """
        Returns the platform name identifier.

        This property should return a string that identifies the platform (e.g., 'linux', 'windows', 'svos').

        Returns:
            str: The platform name identifier.

        Raises:
            NotImplementedError: If the property is not implemented in a subclass.
        """
        raise NotImplementedError(
            "The platform_name property must be implemented in a subclass."
        )

    @property
    @abstractmethod
    def is_unix(self):
        """
        Returns whether the platform is Unix-based.

        This property determines if the current operating system is Unix-based
        (e.g., Linux, Svos) or not (e.g., Windows).

        Returns:
            bool: True if the platform is Unix-based, False otherwise.

        Raises:
            NotImplementedError: If the property is not implemented in a subclass.
        """
        pass

    def safe_kill(
        self, thread_obj: threading.Thread, sig_type: int = signal.SIGINT
    ):
        """
        Safely kills a thread or process.

        This method sends a signal (default: SIGINT) to the specified thread or process
        and handles any failures quietly. It is used to gracefully terminate threads
        or processes that may have already ended or failed to start.

        Args:
            thread_obj (threading.Thread): The thread object to terminate.
            sig_type (int, optional): The signal type to send. Defaults to `signal.SIGINT`.

        Returns:
            None
        """
        try:
            # By default, send Ctrl-C to get the data from the tests
            os.kill(thread_obj.pid, sig_type)
        except (ProcessLookupError, TypeError, AttributeError, OSError):
            # Some of the instances may have already ended or failed to start
            # and did not have a PID
            pass

    @staticmethod
    def get_highest_cpu_instruction_set():
        """Check for CPU features executing assembly instructions to return the highest set of instructions.
        :return: str
        """
        cpuid = CPUID()
        leaf1_regs = cpuid.get_flag_dynamic(1, 0)
        leaf7_regs = cpuid.get_flag_dynamic(7, 0)

        # Check for AVX512F in EBX register of leaf 7
        if leaf7_regs["ebx"] & (1 << 16) > 0:
            return "avx512"
        # Check for AVX in ECX register of leaf 1
        elif leaf1_regs["ecx"] & (1 << 28) > 0:
            return "avx"
        # Check for SSE in EDX register of leaf 1
        elif leaf1_regs["edx"] & (1 << 25) > 0:
            return "sse"
        else:
            return "legacy"

    @abstractmethod
    def set_priority(self, value: int):
        """
        Converts a priority value to a 'nice' value.

        This method is used to adjust the priority of a process or thread in an
        OS-specific way. The implementation should return the command used to set
        the priority and the resulting 'nice' value.

        Args:
            value (int): The priority value to convert.

        Returns:
            list: A list containing the command used to set the priority and the
            resulting 'nice' value.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        pass

    @abstractmethod
    def generate_os_command(self, test_case, mem_per_instance, lpu):
        """
        Generates an OS-specific command for executing a tool.

        This method is used to create a command that can be executed in the operating
        system to run a specific tool with the given parameters.

        Args:
            test_case (str): The test case to execute.
            mem_per_instance (float): The memory allocated per instance.
            lpu (int): The logical processing unit (LPU) to use.

        Returns:
            str: The generated OS-specific command.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        pass

    @abstractmethod
    def stop_thread(self, curr_thread):
        """
        Stops a thread in an OS-specific way.

        This method implements the specific way of terminating a single thread
        in the operating system.

        Args:
            curr_thread (threading.Thread): The thread to stop.

        Returns:
            None

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        pass

    @abstractmethod
    def halt_thread(self, curr_thread):
        """
        Halts a thread in an OS-specific way.

        This method implements the specific way of pausing a single thread
        in the operating system.

        Args:
            curr_thread (threading.Thread): The thread to halt.

        Returns:
            None

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        pass

    @abstractmethod
    def resume_thread(self, curr_thread):
        """
        Resumes a thread in an OS-specific way.

        This method implements the specific way of resuming a single thread
        in the operating system.

        Args:
            curr_thread (threading.Thread): The thread to resume.

        Returns:
            None

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        pass
