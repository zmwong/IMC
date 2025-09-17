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
import abc
import threading


class BasePlugin(abc.ABC):
    """
    Abstract base class for all plugins.

    This class defines the standard interface that all plugins must implement.
    It ensures that plugins can be loaded, executed, and cleaned up in a
    consistent manner by the SystemHandler.
    """

    def __init__(self):
        """
        Initializes the plugin instance.
        """
        self._thread = None
        self._stop_event = threading.Event()

    @abc.abstractmethod
    def initialize(self):
        """
        Initializes the plugin.

        This method is called once when the plugin is loaded. It should be
        used for any setup tasks, such as loading libraries or reading
        configuration.
        """
        pass

    @abc.abstractmethod
    def run(self):
        """
        Executes the main logic of the plugin.

        This method contains the primary functionality of the plugin. It may
        be called in a separate thread or process depending on the application's
        architecture.
        """
        pass

    @abc.abstractmethod
    def cleanup(self):
        """
        Performs cleanup operations for the plugin.

        This method is called before the application exits to allow the plugin
        to release resources, such as closing files or unloading libraries.
        """
        pass

    def _execute(self):
        """
        Executes the plugin's full lifecycle.

        Initializes the plugin, runs it in a loop until a stop signal is
        received, and then cleans up resources.
        """
        self.initialize()
        self.run()
        self.cleanup()

    def start(self):
        """
        Starts the plugin in a new thread.

        This method is a convenience method that calls the `run` method in a
        separate thread. It can be overridden if additional startup logic is
        needed.
        """
        self._thread = threading.Thread(target=self._execute)
        self._thread.start()

    def stop(self):
        """
        Signals the plugin to stop its execution loop.
        """
        self._stop_event.set()

    def join(self, timeout=None):
        """
        Waits for the plugin thread to complete.

        Args:
            timeout (float, optional): The timeout in seconds to wait for the
                                     thread to complete. Defaults to None.
        """
        if self._thread:
            self._thread.join(timeout)
