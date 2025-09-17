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

from abc import ABC, abstractmethod
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


class AbstractRunnable(ABC):
    """Abstract base class for all tool managers defining common interface methods."""

    def __init__(self, distribution, executor, tool_manager):
        super().__init__()
        self.distribution = distribution
        self.executor = executor
        self.tool_manager = tool_manager
        self.results = None

    @abstractmethod
    def _execute(self):
        """Internal method to execute the tool with specific execution requirements."""
        raise NotImplementedError(
            "Subclasses of AbstractRunnable must implement _execute()."
        )

    def execute(self):
        """Execute the tool with specific execution requirements."""
        try:
            self.tool_manager.logger.start_execution()
            self.tool_manager.logger.start_phase("SETUP")
            self.tool_manager.logger.log_setup("Setting up tool environment...")
            self.tool_manager.setup()
            self.tool_manager.logger.end_phase("SETUP")
            self.tool_manager.logger.start_phase("INITIALIZATION")
            self.tool_manager.initialize()
            self.tool_manager.logger.end_phase("INITIALIZATION")
            self._execute()
        except Exception as e:
            error_str = str(e)
            LogManager().log(
                self.tool_manager.logger_name,
                LogManagerThread.Level.ERROR,
                f"Error: {error_str}",
            )
            self.tool_manager.tool_data.data["execution_error"] = error_str
