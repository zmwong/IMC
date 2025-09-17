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
This module provides the definition for the `DefaultThread` class.

The `DefaultThread` class extends the `BaseThread` class and provides a concrete
implementation for executing subprocesses. It manages the execution of commands
and handles the communication between threads and queues.
"""

import queue
from scripts.libs.components.os_system.abstract_system import AbstractSystem
from scripts.libs.components.executors.base_thread import BaseThread


class DefaultThread(BaseThread):
    """
    A default implementation of the `BaseThread` class.

    The `DefaultThread` class is responsible for executing subprocesses using
    the `BaseThread`'s `create_subprocess` method. It manages the execution of
    commands and facilitates communication between threads and queues.

    Attributes:
        exec_queue (list): The list of commands to execute as a subprocess.
        data_queue (queue.Queue): A queue to store the results of the subprocess.
        pid_queue (queue.Queue): A queue to store the PID of the subprocess.
        os_system (AbstractSystem): The operating system abstraction for managing
            subprocess creation flags.
        logger_name (str): The name of the logger instance for logging messages.
    """

    def __init__(
        self,
        exec_list: list,
        data_queue: queue.Queue,
        pid_queue: queue.Queue,
        os_system: AbstractSystem,
    ):
        """
        Initializes the DefaultThread class.

        This constructor initializes the thread with the necessary attributes
        for managing subprocess execution and communication.

        Args:
            exec_list (list): The list of commands to execute as a subprocess.
            data_queue (queue.Queue): A queue to store the results of the subprocess.
            pid_queue (queue.Queue): A queue to store the PID of the subprocess.
            os_system (AbstractSystem): The operating system abstraction for managing
                subprocess creation flags.

        Example:
            ```
            exec_list = ["python", "script.py"]
            data_queue = queue.Queue()
            pid_queue = queue.Queue()
            os_system = AbstractSystem()

            thread = DefaultThread(exec_list, data_queue, pid_queue, os_system)
            thread.start()
            ```
        """
        super().__init__()
        self.exec_queue = exec_list
        self.data_queue = data_queue
        self.pid_queue = pid_queue
        self.os_system = os_system

    def run(self):
        """
        Executes the thread's main logic.

        This method calls the `create_subprocess` method from the `BaseThread`
        class to execute the commands in the `exec_queue`. It manages the
        communication between the subprocess and the provided queues.

        Example:
            ```
            thread = DefaultThread(exec_list, data_queue, pid_queue, os_system)
            thread.start()
            ```
        """
        self.create_subprocess(
            self.exec_queue,
            self.data_queue,
            self.pid_queue,
            self.os_system,
        )
