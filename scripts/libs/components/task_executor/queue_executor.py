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
This module handles the definition for the queue executor.

The `QueueExecutor` class extends the `AbstractExecutor` class and implements
a queue-based execution system. It creates threads to execute commands from a
queue, where each thread takes a task, executes it, and then retrieves the next
task until all tasks are completed.
"""

from scripts.libs.components.task_executor.abstract_executor import (
    AbstractExecutor,
)
import queue
import time
import subprocess
import collections
from scripts.libs.definitions.imc import TOOL_NAME
from scripts.libs.system_handler import SystemHandler
from scripts.libs.components.runnable_threads.queue_thread import QueueThread
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)
from scripts.libs.components.os_system.abstract_system import AbstractSystem


class QueueExecutor(AbstractExecutor):
    """
    Implements the AbstractExecutor interface using a queue-based execution system.

    The `QueueExecutor` creates threads to execute commands from a queue. Each thread
    retrieves a task from the queue, executes it, and then retrieves the next task
    until all tasks are completed. The results of each execution are passed to the
    result queue for further processing.

    Attributes:
        threads (list): A list of threads managed by the executor.
    """

    def __init__(self, tool_data):
        """
        Initializes the QueueExecutor class.

        Args:
            tool_data (object): The data handler object for the tool, containing
                parsed arguments, environment details, and logger.
        """
        super().__init__(tool_data)

    def _run_cmd(
        self,
        exec_list: list,
        data_queue: queue.Queue,
        pid_queue: queue.Queue,
        os_system: AbstractSystem,
    ):
        """Execute the tool processes using subprocess, and retrieve the information"""
        creation_flags = os_system.creation_flags
        test_result = collections.namedtuple(
            "TestResult", "pid stdout stderr exitcode"
        )

        with subprocess.Popen(
            exec_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            encoding="utf-8",
            creationflags=creation_flags,
        ) as proc:
            LoggerManager().log(
                "SYS",
                LoggerManagerThread.Level.DEBUG,
                "_run_cmd(): PID-%d about to start using %s",
                proc.pid,
                " ".join(exec_list),
                thread_name=f"Thread-PID-{proc.pid}",
                phase="EXECUTION",
            )
            pid_queue.put(proc.pid)  # tell the parent our pid
            stdout = self._pipe_reader(proc.stdout)
            stderr = self._pipe_reader(proc.stderr)
            proc.wait()
            data_queue.put(
                test_result(
                    pid=proc.pid,
                    stdout=stdout,
                    stderr=stderr,
                    exitcode=proc.returncode,
                )
            )

    def executeInstances(self, commands_list):
        """
        Executes tool instances using a queue-based system.

        This method creates a queue containing the commands to execute and spawns
        threads to process the commands. Each thread retrieves a task from the queue,
        executes it, and then retrieves the next task until the queue is empty. The
        results of each execution are passed to the result queue for further processing.


        Args:
            commands_list (list): A list of commands to execute.


        Raises:
            ValueError: If the `commands_list` is empty.


        """
        if not commands_list:
            raise ValueError("No LPUs were detected!")

        lpu_count = len(self.tool_manager.tool_data.parsed_args.lpus)
        cmd_count = len(commands_list)
        tool_name = self.tool_manager.tool_data.TOOL_NAME

        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.INFO,
            f"Starting {lpu_count} thread instances to execute {cmd_count} test cases using the {tool_name} tool.",
        )

        cmd_queue = queue.Queue(maxsize=cmd_count)
        for command in commands_list:
            cmd_queue.put(command)

        self.threads = []
        pid_queue = self.tool_manager.tool_data.data["pid_queue"]
        result_queue = self.tool_manager.tool_data.data["result_queue"]
        os_system = SystemHandler().os_system

        for i in range(lpu_count):
            thread = QueueThread(
                cmd_queue,
                result_queue,
                pid_queue,
                os_system,
            )
            self.threads.append(thread)
            thread.start()
            thread.pid = None

            # Retrieve the PID of the thread
            try:
                thread.pid = pid_queue.get(timeout=60)
                LoggerManager().log(
                    "SYS",
                    LoggerManagerThread.Level.DEBUG,
                    f"{thread.name} has started PID-{thread.pid}!",
                    thread_name=thread.name,
                    phase="EXECUTION",
                )
            except queue.Empty:
                LoggerManager().log(
                    "SYS",
                    LoggerManagerThread.Level.ERROR,
                    f"{thread.name} failed to start {tool_name}.",
                    thread_name=thread.name,
                    phase="EXECUTION",
                )

        timeout_seconds = self.tool_manager.tool_data.parsed_args.timeout
        end_time = time.time() + (timeout_seconds * 60)

        self.watch_threads(end_time)

        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.INFO,
            f"All {tool_name} execution instances have completed.",
            phase="EXECUTION",
        )

        self.tool_manager.tool_data.data["execution_completed"] = True

        if hasattr(self.tool_manager, "logger"):
            if (
                hasattr(
                    self.tool_manager.tool_data.parsed_args, "time_to_execute"
                )
                and self.tool_manager.tool_data.parsed_args.time_to_execute
            ):
                time_limit = (
                    self.tool_manager.tool_data.parsed_args.time_to_execute
                )
                self.tool_manager.logger.log_execution(
                    f"Time-based execution completed after configured time ({time_limit} second(s))"
                )
            else:
                self.tool_manager.logger.log_execution(
                    "All execution instances have completed"
                )
