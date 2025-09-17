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
import subprocess
import time
import os
from scripts.libs.plugins.base_plugin import BasePlugin
from scripts.libs.loggers.log_manager import LogManager, LogManagerThread
from scripts.libs.loggers import Level


class PCMMemoryPlugin(BasePlugin):
    """Plugin to record memory bandwidth using the Intel PCM memory tool.

    This plugin launches the PCM memory measurement tool as a subprocess and logs
    bandwidth statistics to a CSV file.
    """

    def __init__(
        self,
        command,
        delay=1,
    ):
        """
        Initializes the PCM Memory Plugin.

        Args:
            command (str): Path to the PCM memory tool executable.
            delay (int): Sampling interval in seconds.
        """
        super().__init__()
        self._command = [
            command,
            str(delay),
            f"-csv={os.path.join(LogManager().get_execution_log_dir(), 'pcm_memory.csv')}",
            "-f",
            "-silent",
        ]
        self._process = None
        self.logger_name = "PCM-MEM"
        LogManager().create_logger(self.logger_name, Level.INFO)
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"Utilizing PCM Memory path: {command}",
        )

    def initialize(self):
        """Initializes logging for the PCM memory plugin.

        Logs the initialization message for the PCM memory plugin.
        """
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "Initializing PCM Memory Plugin...",
        )

    def run(self):
        """Launches the PCM memory tool and logs its output until a stop signal is received.

        Runs the configured PCM memory measurement tool as a subprocess and waits for
        a stop event before terminating the subprocess.

        Raises:
            OSError: If the PCM tool cannot be started.
        """
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"Starting PCM memory measurement with command: {' '.join(self._command)}",
        )

        try:
            self._process = subprocess.Popen(self._command)
        except OSError as e:
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.ERROR,
                f"Failed to start PCM memory tool: {e}",
            )
            return
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        finally:
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.INFO,
                "Stop signal received, terminating PCM tool",
            )
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    LogManager().log(
                        self.logger_name,
                        LogManagerThread.Level.ERROR,
                        "PCM tool did not terminate in time; killing",
                    )
                    self._process.kill()
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "PCM memory measurement stopped",
        )

    def cleanup(self):
        """Terminates the PCM memory subprocess and cleans up resources.

        Logs cleanup actions and ensures the PCM subprocess is terminated.
        """
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "Cleaning up PCM memory plugin",
        )
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait()
