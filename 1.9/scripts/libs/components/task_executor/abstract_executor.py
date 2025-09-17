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
This module provides a common interface for executing tool instances.

The `AbstractExecutor` class defines the base implementation for managing the
execution of tool instances, including thread management, signal handling, and
timeout monitoring. Subclasses must implement the `executeInstances` method to
define the specific execution behavior.
"""

import queue
import time
import signal
from abc import ABC, abstractmethod
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.system_handler import SystemHandler
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)
from scripts.libs.components.os_system.abstract_system import AbstractSystem


class AbstractExecutor(ABC):
    """
    Abstract base class for executing tool instances.

    This class provides a base implementation for managing the execution of tool
    instances, including thread management, signal handling, and timeout monitoring.
    Subclasses must implement the `executeInstances` method to define the specific
    execution behavior.

    Attributes:
        active_instances (list): A class-level list of all active executor instances.
        tool_manager (object): An object responsible for managing tool-specific data and operations.
        signalMap (dict): A mapping of signals to their respective handler methods.
        threads (list): A list of threads managed by the executor.
    """

    active_instances = []

    def __init__(self, tool_manager) -> None:
        """
        Initializes the AbstractExecutor class.

        This constructor sets up signal handling, initializes thread management,
        and prepares data queues for managing tool execution.

        Args:
            tool_data (object): The data handler object for the tool, containing
                parsed arguments, environment details, and logger.
        """
        super().__init__()
        AbstractExecutor.active_instances.append(self)
        self.tool_manager = tool_manager
        self.signalMap = {
            signal.SIGINT: self.stop_threads,
        }
        if SystemHandler().os_system.platform_name != "windows":
            self.signalMap[signal.SIGTSTP] = self.halt_threads
            self.signalMap[signal.SIGCONT] = self.resume_threads
        self.threads = []
        self.tool_manager.tool_data.data["result_queue"] = queue.Queue()
        self.tool_manager.tool_data.data["pid_queue"] = queue.Queue()
        self.tool_manager.tool_data.data["data_from_queue"] = []
        self.tool_manager.tool_data.data["taskkill_result_list"] = []

    @classmethod
    def get_active_instances(cls):
        """
        Retrieves all active executor instances.

        Returns:
            list: A list of active executor instances.
        """
        return cls.active_instances

    def watch_threads(self, end_time):
        """
        Monitors the threads for activity and handles timeouts.

        This method monitors all threads for activity, checks for timeout conditions,
        and processes results from the result queue. If a timeout occurs or an error
        is detected, it stops all threads.

        Args:
            end_time (float): The timestamp indicating when the timeout period ends.
        """
        timed_out = False

        thread_count = len(self.threads)

        timeout_msg = None
        if self.tool_manager.tool_data.parsed_args.timeout:
            timeout_msg = (
                "The timeout period of %s minute(s) has been reached, stopping all %s instances."
                % (
                    self.tool_manager.tool_data.parsed_args.timeout,
                    self.tool_manager.tool_data.TOOL_NAME,
                )
            )

        while True:
            if thread_count > 0 and not any(x.is_alive() for x in self.threads):
                break

            if (
                thread_count == 0
                and self.tool_manager.tool_data.data["result_queue"].empty()
            ):
                break

            if (
                not timed_out
                and self.tool_manager.tool_data.parsed_args.timeout
                and time.time() >= end_time
            ):
                timed_out = True
                self.tool_manager.tool_data.data["time_limit_reached"] = True

                LoggerManager().log(
                    "SYS", LoggerManagerThread.Level.INFO, timeout_msg
                )

                LoggerManager().set_preserve_loggers(["IMC", "SYS"])

                logger = getattr(self.tool_manager, "logger", None)
                if logger and hasattr(logger, "log_timeout"):
                    logger.log_timeout(
                        self.tool_manager.tool_data.parsed_args.timeout,
                        unit="minute(s)",
                    )
                self.stop_threads()

            queue_emptied = False
            while not queue_emptied:
                try:
                    if not self.tool_manager.tool_data.data[
                        "result_queue"
                    ].empty():
                        current_data = self.tool_manager.tool_data.data[
                            "result_queue"
                        ].get(block=False)

                        if (
                            SystemHandler().os_system.platform_name.upper()
                            == "WINDOWS"
                        ):
                            for (
                                taskkill_result
                            ) in self.tool_manager.tool_data.data[
                                "taskkill_result_list"
                            ]:
                                if (
                                    taskkill_result.exitcode == 0
                                    and current_data.pid == taskkill_result.pid
                                ):
                                    current_data = current_data._replace(
                                        exitcode=ExitCode.TOOL_ENDED_USING_TASKKILL
                                    )
                                    break
                        thread_name = f"Thread-PID-{current_data.pid}"
                        LoggerManager().log(
                            "SYS",
                            LoggerManagerThread.Level.DEBUG,
                            "New data in the finished queue from PID-%d"
                            % current_data.pid,
                            thread_name=thread_name,
                        )

                        if (
                            self.tool_manager.tool_data.parsed_args.stop_on_error
                            and current_data.exitcode != int(ExitCode.OK)
                        ):
                            LoggerManager().log(
                                "SYS",
                                LoggerManagerThread.Level.ERROR,
                                "Instance PID-%d has ended prematurely!"
                                % current_data.pid,
                                thread_name=f"Thread-PID-{current_data.pid}",
                            )
                            self.stop_threads()

                        self.tool_manager.tool_data.data[
                            "data_from_queue"
                        ].append(current_data)
                    else:
                        queue_emptied = True
                except queue.Empty:
                    queue_emptied = True

    def stop_threads(self, *args):
        """
        Stops all active threads.

        This method loops through all active threads and stops them using the
        respective OS signal. If threads fail to stop gracefully, they are forcefully
        terminated.

        Args:
            *args: Additional arguments passed by the signal handler.
        """
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.INFO,
            "Ctrl-C detected!  Stopping all instances of %s.",
            self.tool_manager.tool_data.TOOL_NAME,
            phase="EXECUTION",
        )
        for curr_thread in self.live_threads():
            LoggerManager().log(
                "SYS",
                LoggerManagerThread.Level.DEBUG,
                "Stopping %s" % curr_thread.name,
                thread_name=curr_thread.name,
                phase="EXECUTION",
            )
            SystemHandler().os_system.safe_kill(
                curr_thread, SystemHandler().os_system.safe_signal
            )
        time.sleep(5)

        for curr_thread in self.live_threads():
            curr_thread.join(1)
            if curr_thread.is_alive():
                LoggerManager().log(
                    "SYS",
                    LoggerManagerThread.Level.WARNING,
                    f"Forcefully terminating thread: {curr_thread.name}",
                    thread_name=curr_thread.name,
                    phase="EXECUTION",
                )
                taskkill_result = SystemHandler().os_system.stop_thread(
                    curr_thread
                )
                if taskkill_result:
                    self.tool_manager.tool_data.data[
                        "taskkill_result_list"
                    ].append(taskkill_result)

        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.DEBUG,
            "All execution threads have been stopped.",
            phase="EXECUTION",
        )

    def halt_threads(self, *args):
        """
        Halts all active threads by sending a SIGSTOP signal.

        Args:
            *args: Additional arguments passed by the signal handler.
        """
        for curr_thread in self.live_threads():
            if curr_thread.proc:
                curr_thread.proc.send_signal(signal.SIGSTOP)

    def resume_threads(self, *args):
        """
        Resumes all halted threads by sending a SIGCONT signal.

        Args:
            *args: Additional arguments passed by the signal handler.
        """
        for curr_thread in self.live_threads():
            if curr_thread.proc:
                curr_thread.proc.send_signal(signal.SIGCONT)

    def live_threads(self):
        """
        Retrieves a list of live threads managed by the executor.

        Returns:
            list: A list of live threads.
        """
        return [x for x in self.threads if x.is_alive()]

    @abstractmethod
    def executeInstances(self, commands_list):
        """
        Executes tool instances in a specific manner.

        This method must be implemented by subclasses to define the specific
        behavior for executing tool instances. Active threads must be registered
        in the `self.threads` list and cleaned up when execution is complete.

        Args:
            commands_list (list): A list of commands to execute.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        pass
