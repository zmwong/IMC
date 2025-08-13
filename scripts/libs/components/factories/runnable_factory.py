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
"""
This module provides a scalable way of creating runnable objects through a single
interface. It uses a factory pattern to create runnable objects and assigns the
necessary components dynamically using lazy loading.
"""

from scripts.libs.runnables.imc_runnable import ImcRunnable
from scripts.libs.utils.lazy_loader import LazyLoader
from scripts.libs.tools.tool_managers.imc_tool_manager import ImcToolManager


class RunnableFactory:
    """
    A factory class for creating runnable objects.

    The `RunnableFactory` class is responsible for creating runnable objects
    based on the tool specified. It dynamically assigns the necessary components
    (e.g., distribution and executor) using lazy loading. Currently, only the
    IMC tool is supported.

    Attributes:
        None
    """

    def create(self, tool, args_string):
        """
        Creates a runnable object for the specified tool.

        This method creates a runnable object for the given tool and assigns
        the necessary components (e.g., distribution and executor) dynamically
        using lazy loading. Currently, only the IMC tool is supported.

        Args:
            tool (str): The name of the tool for which the runnable is being created.
                        Currently, only "IMC" is supported.
            args_string (str): A string of arguments to be passed to the tool's data handler.

        Returns:
            ImcRunnable: A runnable object configured for the specified tool.

        Raises:
            ValueError: If the specified tool is not supported.

        Example:
            To create a runnable for the IMC tool:
            ```
            factory = RunnableFactory()
            runnable = factory.create("IMC", "--arg1 value1 --arg2 value2")
            ```

        Disclaimer:
            This method currently supports only the IMC tool. Future tools may
            require additional implementations.
        """
        if tool == "IMC":
            tool_manager = ImcToolManager(args_string)
            runnable = ImcRunnable(tool_manager)
            # Assign the distribution dynamically using lazy loading
            # Pass the singleton instance directly for better performance
            runnable.distribution = LazyLoader.load(
                "scripts.libs.components.distributions.cycle_distribution",
                "CycleDistribution",
            )(tool_manager)

            # Assign the executor dynamically based on the execution type
            if tool_manager.tool_data.parsed_args.executionType == "queue":
                runnable.executor = LazyLoader.load(
                    "scripts.libs.components.task_executor.queue_executor",
                    "QueueExecutor",
                )(tool_manager)
            elif tool_manager.tool_data.parsed_args.executionType == "batch":
                runnable.executor = LazyLoader.load(
                    "scripts.libs.components.task_executor.batch_executor",
                    "BatchExecutor",
                )(tool_manager)

            return runnable
        else:
            raise ValueError(f"Unsupported tool: {tool}")
