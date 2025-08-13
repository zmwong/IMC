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
This module provides the specific definition for an IMC runnable.
"""
import argparse
from typing import List
from scripts.libs.utils.logging import get_log_level_from_verbosity

from scripts.libs.components.distributions.abstract_distribution import (
    AbstractDistribution,
)
from scripts.libs.components.task_executor.abstract_executor import (
    AbstractExecutor,
)
from scripts.libs.runnables.runnable import AbstractRunnable
from scripts.libs.tools.tool_managers.imc_tool_manager import ImcToolManager
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)
from scripts.libs.utils.structured_logger import StructuredLogger
from scripts.libs.system_handler import SystemHandler
from scripts.libs.definitions.exit_codes import ExitCode


class ImcRunnable(AbstractRunnable):
    """
    A runnable implementation for the IMC tool.

    The IMCRunnable class is a specific implementation of the Runnable interface, the tool
    is executed when the execute is called. Before the execution, the files and binary are
    verified, and then the commands are generated.

    Attributes:
    Tool_manager (object): An object responsible for managing tool-specific data and operations.
    Distribution (AbstractDistribution): The distribution for how are commands going to be
    generated.
    Executor (AbstractExecutor): The executor that will specify on how instances are going
    to be executed.

    To use this class, the user must provide the necessary components, or use the
    RunnableFactory to create the runnable object.
    """

    def __init__(self, tool_manager) -> None:
        self.distribution: AbstractDistribution = None
        self.executor: AbstractExecutor = None
        self.tool_manager = tool_manager
        self.results = None

        verbosity = SystemHandler().get_verbosity()
        self.logger_name = "IMC"
        log_level = get_log_level_from_verbosity(verbosity)

        # Initialize the IMC logger
        LoggerManager().create_logger(
            name=self.logger_name,
            log_level=log_level,
        )

        self.logger = StructuredLogger(logger_name=self.logger_name)

    @staticmethod
    def parse_args_list(argv: List[str]) -> argparse.Namespace:
        """
        Delegates argument parsing to the ImcToolManager.

        Args:
            argv: Command-line arguments

        Returns:
            Parsed arguments namespace
        """
        return ImcToolManager.parse_args_list(argv)

    def execute(self):
        """
        Executes the IMC tool with high-performance logging.

        Returns:
            The result of tool execution
        """
        result = None
        self.tool_manager.tool_data.data["time_limit_reached"] = False
        self.tool_manager.tool_data.data["execution_completed"] = False

        tm = self.tool_manager
        logger = self.logger

        logger.start_execution()

        try:
            logger.start_phase("SETUP")
            logger.log_setup("Setting up tool environment...")
            tm.setup()
            logger.end_phase("SETUP")

            logger.start_phase("INITIALIZATION")

            tm.initialize()

            commands = self.distribution.generate_commands()
            command_count = len(commands) if commands else 0

            init_message = f"Generated {command_count} execution commands"

            parsed_args = tm.tool_data.parsed_args
            if (
                hasattr(parsed_args, "time_to_execute")
                and parsed_args.time_to_execute
            ):
                time_limit = parsed_args.time_to_execute
                init_message += (
                    f" | Time-based execution: {time_limit} second(s)"
                )

            logger.log_initialization(init_message)
            logger.end_phase("INITIALIZATION")

            logger.start_phase("EXECUTION")
            logger.log_execution("Executing IMC instances...")

            LoggerManager().set_preserve_loggers(
                [self.logger_name, "IMC", "SYS"]
            )

            self.executor.executeInstances(commands)

            if not tm.tool_data.data.get("time_limit_reached", False):
                logger.log_execution("Execution completed normally")

            logger.end_phase("EXECUTION")

        except Exception as e:
            error_str = str(e)
            LoggerManager().log(
                self.logger_name,
                LoggerManagerThread.Level.ERROR,
                f"Error: {error_str}",
            )
            tm.tool_data.data["execution_error"] = error_str

        try:
            if tm.tool_data.data.get("time_limit_reached", False):
                if not LoggerManager().manager_thread.has_logger(
                    self.logger_name
                ):
                    LoggerManager().create_logger(
                        name=self.logger_name,
                        log_level=LoggerManagerThread.Level.INFO,
                    )

            logger.start_phase("POST_EXECUTION")

            debug_log_file = LoggerManager().get_debug_log_file()
            if debug_log_file:
                logger.log_post_execution(
                    f"Complete debug logs have been written to: {debug_log_file}"
                )
                logger.log_post_execution(
                    "This file contains all detailed logs including those not shown in the terminal."
                )

            if tm.tool_data.data.get("time_limit_reached", False) and hasattr(
                parsed_args, "time_to_execute"
            ):
                logger.log_post_execution(
                    f"Processing results after time-based completion"
                )
            elif "execution_error" in tm.tool_data.data:
                logger.log_post_execution(
                    "Processing results after execution error"
                )
            else:
                logger.log_post_execution("Processing execution results...")

            result = tm.post_process()
            logger.end_phase("POST_EXECUTION")

            was_successful = ("execution_error" not in tm.tool_data.data) and (
                result == ExitCode.OK
            )
            logger.end_execution(success=was_successful, exit_code=result)

            LoggerManager().log(
                self.logger_name,
                LoggerManagerThread.Level.INFO,
                "All execution logs completed",
            )

        except Exception as post_error:
            error_str = str(post_error)
            LoggerManager().log(
                self.logger_name,
                LoggerManagerThread.Level.ERROR,
                f"Post-processing error: {error_str}",
            )
            logger.end_execution(success=False, exit_code=str(post_error))
            raise

        return result
