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
This module contains the definition of a thread that executes tasks sequentially from
a queue.

The `QueueThread` class extends the `BaseThread` class and provides functionality
to execute subprocesses by retrieving commands from a queue. The thread continues
execution until the queue is empty.
"""

import queue
from scripts.libs.components.os_system.abstract_system import AbstractSystem
from scripts.libs.components.executors.base_thread import BaseThread


class QueueThread(BaseThread):
    """
    A thread that executes subprocesses sequentially from a queue.

    The `QueueThread` class retrieves commands from a queue and executes them
    as subprocesses using the `BaseThread`'s `create_subprocess` method. The
    thread continues execution until the queue is empty.

    Attributes:
        exec_queue (queue.Queue): A queue containing the commands to execute.
        data_queue (queue.Queue): A queue to store the results of the subprocesses.
        pid_queue (queue.Queue): A queue to store the PIDs of the subprocesses.
        os_system (AbstractSystem): The operating system abstraction for managing
            subprocess creation flags.
        LOGGER (logging.Logger): The logger instance for logging messages.
    """

    def __init__(
        self,
        exec_queue: queue.Queue,
        data_queue: queue.Queue,
        pid_queue: queue.Queue,
        os_system: AbstractSystem,
    ):
        """
        Initializes the QueueThread class.

        This constructor initializes the thread with the necessary attributes
        for managing subprocess execution and communication.

        Args:
            exec_queue (queue.Queue): A queue containing the commands to execute.
            data_queue (queue.Queue): A queue to store the results of the subprocesses.
            pid_queue (queue.Queue): A queue to store the PIDs of the subprocesses.
            os_system (AbstractSystem): The operating system abstraction for managing
                subprocess creation flags.
            LOGGER (logging.Logger): The logger instance for logging messages.

        Example:
            ```
            exec_queue = queue.Queue()
            data_queue = queue.Queue()
            pid_queue = queue.Queue()
            os_system = AbstractSystem()
            LOGGER = logging.getLogger("QueueThread")

            thread = QueueThread(exec_queue, data_queue, pid_queue, os_system, LOGGER)
            thread.start()
            ```
        """
        super().__init__()
        self.exec_queue = exec_queue
        self.data_queue = data_queue
        self.pid_queue = pid_queue
        self.os_system = os_system

    def run(self):
        """
        Executes commands from the queue as subprocesses.

        This method retrieves commands from the exec_queue and executes them
        as subprocesses using the create_subprocess method from the BaseThread
        class. The thread continues execution until the queue is empty.

        Example:
            ```
            thread = QueueThread(exec_queue, data_queue, pid_queue, os_system, LOGGER)
            thread.start()
            ```
        """

        while not self.exec_queue.empty():
            exec_list = self.exec_queue.get(block=False)
            self.create_subprocess(
                exec_list,
                self.data_queue,
                self.pid_queue,
                self.os_system,
            )
