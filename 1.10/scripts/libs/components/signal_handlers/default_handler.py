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
This module provides a default way for handling signals in the runner.

The `defaultSignalHandler` class provides support for handling signals such as
`SIGINT`, `SIGTSTP`, and `SIGCONT` on Linux-based systems. It ensures that signals
are relayed to active executors, allowing them to manage their respective threads.
"""

import signal
from scripts.libs.components.executors.abstract_executor import (
    AbstractExecutor,
)
from scripts.libs.system_handler import SystemHandler


class defaultSignalHandler:
    """
    Default signal handler for managing signals in the runner.

    The `defaultSignalHandler` class is instantiated in the main thread of the runner,
    as the `signal` module requires signals to be handled in the main thread. When a
    signal is received, it is relayed to all active executors, which handle their
    respective threads accordingly.

    Attributes:
        None
    """

    def __init__(self) -> None:
        """
        Initializes the defaultSignalHandler class.

        This constructor sets up signal handling for `SIGINT`, `SIGTSTP`, and `SIGCONT`.
        On Windows systems, only `SIGINT` is supported, as `SIGTSTP` and `SIGCONT` are
        not available.

        Example:
            ```
            signal_handler = defaultSignalHandler()
            ```

        Raises:
            ValueError: If the signal handling setup fails.
        """
        signal.signal(signal.SIGINT, self.handle_signal)
        if SystemHandler().os_system.platform_name != "windows":
            signal.signal(signal.SIGTSTP, self.handle_signal)
            signal.signal(signal.SIGCONT, self.handle_signal)
            # Add memory error emergency signals
            signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signalNum, frame):
        """
        Handles incoming signals and relays them to active executors.

        This method is called whenever a signal is received. It iterates through all
        active executors and invokes the appropriate signal handler from their [signalMap](http://_vscodecontentref_/1).

        Args:
            signalNum (int): The signal number (e.g., [SIGINT](http://_vscodecontentref_/2), [SIGTSTP](http://_vscodecontentref_/3), [SIGCONT](http://_vscodecontentref_/4)).
            frame (frame object): The current stack frame (provided by the [signal](http://_vscodecontentref_/5) module).

        Example:
            ```
            signal_handler = defaultSignalHandler()
            signal_handler.handle_signal(signal.SIGINT, None)
            ```

        Raises:
            KeyError: If the signal number is not found in the executor's [signalMap](http://_vscodecontentref_/6).
        """
        for executor in AbstractExecutor.active_instances:
            if signalNum in executor.signalMap:
                executor.signalMap[signalNum](signalNum, frame)
