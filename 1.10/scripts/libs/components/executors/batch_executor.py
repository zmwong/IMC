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
This module provides the implementation for executing threads by batches.

The `BatchExecutor` class extends the `AbstractExecutor` class and implements
a batch-based execution system. It divides the commands into batches based on
the number of Logical Processing Units (LPUs) available and executes them sequentially.
"""

from scripts.libs.components.executors.abstract_executor import (
    AbstractExecutor,
)
import time
import queue

from scripts.libs.components.executors.default_thread import (
    DefaultThread,
)
from math import ceil
from scripts.libs.system_handler import SystemHandler
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


class BatchExecutor(AbstractExecutor):
    """
    Implements the AbstractExecutor interface using a batch-based execution system.

    The `BatchExecutor` divides the commands into batches based on the number of
    Logical Processing Units (LPUs) detected in the system. Each batch is executed
    sequentially, and the next batch starts only after all threads in the previous
    batch have completed execution.

    Attributes:
        threads (list): A list of threads managed by the executor.
    """

    def __init__(self, tool_data):
        """
        Initializes the BatchExecutor class.

        Args:
            tool_data (object): The data handler object for the tool, containing
                parsed arguments, environment details, and logger.
        """
        super().__init__(tool_data)

    def executeInstances(self, commands_list):
        """
        Executes tool instances in batches.

        This method divides the commands into batches based on the number of LPUs
        available. Each batch is executed sequentially, and the threads in each batch
        are monitored for activity. If a timeout occurs or a thread fails to start,
        appropriate error handling is performed.

        Args:
            commands_list (list): A list of commands to execute.

        Raises:
            ValueError: If the `commands_list` is empty.

        Example:
            ```
            executor = BatchExecutor(tool_data)
            commands = [["cmd1"], ["cmd2"], ["cmd3"]]
            executor.executeInstances(commands)
            ```

        Process:
            1. Divide the commands into batches based on the number of LPUs.
            2. Start threads for each command in the current batch.
            3. Monitor the threads for activity and handle timeouts or errors.
            4. Repeat for the next batch until all commands are executed.
        """
        if not commands_list:
            raise ValueError("No LPUs were detected!")

        LogManager().log(
            "SYS",
            LogManagerThread.Level.INFO,
            "Starting %s thread instances of the %s tool."
            % (
                len(self.tool_manager.tool_data.parsed_args.lpus),
                self.tool_manager.tool_data.TOOL_NAME,
            ),
        )

        batch_size = len(self.tool_manager.tool_data.parsed_args.lpus)
        num_batches = ceil(len(commands_list) / batch_size)

        LogManager().log(
            "SYS",
            LogManagerThread.Level.INFO,
            "The %s test cases have been divided into %s batches of max %s test cases."
            % (len(commands_list), num_batches, batch_size),
        )

        for batch_num in range(num_batches):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, len(commands_list))
            batch_commands = commands_list[start_index:end_index]

            # Start all threads in the current batch
            batch_threads = []
            for _cmd_args in batch_commands:
                thread = DefaultThread(
                    _cmd_args,
                    self.tool_manager.tool_data.data["result_queue"],
                    self.tool_manager.tool_data.data["pid_queue"],
                    SystemHandler().os_system,
                )
                self.threads.append(thread)
                batch_threads.append(thread)
                thread.start()
                thread.pid = None

                try:
                    thread.pid = self.tool_manager.tool_data.data[
                        "pid_queue"
                    ].get(timeout=60)
                    LogManager().log(
                        "SYS",
                        LogManagerThread.Level.DEBUG,
                        "%s has started PID-%d, Batch-%d!"
                        % (thread.name, thread.pid, batch_num),
                    )
                except queue.Empty:
                    LogManager().log(
                        "SYS",
                        LogManagerThread.Level.ERROR,
                        "%s failed to start %s."
                        % (thread.name, self.tool_manager.tool_data.TOOL_NAME),
                    )

            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                "Batch %s has finished execution." % batch_num,
            )

            # Clear the threads list for the next batch
            self.threads = []

        # Set the 'timeout' now that all batches are complete
        end_time = (
            time.time() + self.tool_manager.tool_data.parsed_args.timeout * 60
        )

        # Monitor all threads for activity (final cleanup if needed)
        if self.threads:
            self.watch_threads(end_time)
        self.tool_manager.tool_data.data["execution_completed"] = True
