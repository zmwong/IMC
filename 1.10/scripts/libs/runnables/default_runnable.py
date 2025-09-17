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
This module provides a default runnable implementation.
"""
import argparse
from typing import List
from scripts.libs.loggers import level_to_verbosity
from scripts.libs.runnables.abstract_runnable import AbstractRunnable
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)
from scripts.libs.loggers.phase_logger import PhaseLogger
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.plugins.pcm.pcm_memory_plugin import PCMMemoryPlugin


class DefaultRunnable(AbstractRunnable):
    """
    A default implementation for a runnable.

    The DefaultRunnable class is a generic implementation of the Runnable interface, the tool
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

    def __init__(self, distribution, executor, tool_manager) -> None:
        super().__init__(distribution, executor, tool_manager)

        # Initialize the logger
        LogManager().create_logger(
            name=self.tool_manager.logger_name,
            log_level=level_to_verbosity(
                self.tool_manager.tool_data.parsed_args.verbosity
            ),
        )

        self.logger = PhaseLogger(logger_name=self.tool_manager.logger_name)

    def parse_args_list(self, argv: List[str]) -> argparse.Namespace:
        """
        Delegates argument parsing to the tool_manager.

        Args:
            argv: Command-line arguments

        Returns:
            Parsed arguments namespace
        """
        return self.tool_manager.parse_args_list(argv)

    def _execute(self):
        """
        Executes the tool with high-performance logging.

        The method manages the execution lifecycle including:
        - Starting performance monitoring (PCM)
        - Generating and executing commands
        - Handling time-based execution limits
        - Post-processing results
        - Cleanup of resources

        Returns:
            The result of tool execution (exit code)
        """
        self.tool_manager.tool_data.data["time_limit_reached"] = False
        self.tool_manager.tool_data.data["execution_completed"] = False
        logger = self.tool_manager.logger
        pcm = None

        if self.tool_manager.tool_data.parsed_args.pcm:
            # Initialize PCM monitoring - don't join immediately so it runs in background
            pcm = PCMMemoryPlugin(
                self.tool_manager.tool_data.parsed_args.pcm_path,
                delay=self.tool_manager.tool_data.parsed_args.pcm_delay,
            )
            pcm.start()

        try:
            commands = self.distribution.generate_commands()
            command_count = len(commands) if commands else 0

            init_message = f"Generated {command_count} execution commands"

            parsed_args = self.tool_manager.tool_data.parsed_args
            if (
                hasattr(parsed_args, "time_to_execute")
                and parsed_args.time_to_execute
            ):
                time_limit = parsed_args.time_to_execute
                init_message += (
                    f" | Time-based execution: {time_limit} second(s)"
                )

            logger.log_initialization(init_message)

            logger.start_phase("EXECUTION")
            logger.log_execution(
                f"Executing {self.tool_manager.TOOL_NAME} instances..."
            )

            LogManager().set_preserve_loggers(
                [self.tool_manager.logger_name, "SYS"]
            )

            self.executor.executeInstances(commands)

            if not self.tool_manager.tool_data.data.get(
                "time_limit_reached", False
            ):
                logger.log_execution("Execution completed normally")

            logger.end_phase("EXECUTION")

        except Exception as e:
            error_str = str(e)
            LogManager().log(
                self.tool_manager.logger_name,
                LogManagerThread.Level.ERROR,
                f"Error: {error_str}",
            )
            self.tool_manager.tool_data.data["execution_error"] = error_str

        try:
            logger.start_phase("POST_EXECUTION")
            exit_code = self.tool_manager.post_process()
            logger.end_phase("POST_EXECUTION")

            was_successful = (
                "execution_error" not in self.tool_manager.tool_data.data
            ) and (exit_code == ExitCode.OK)
            logger.end_execution(success=was_successful, exit_code=exit_code)

            LogManager().log(
                self.tool_manager.logger_name,
                LogManagerThread.Level.INFO,
                "All execution logs completed",
            )

        except Exception as post_error:
            error_str = str(post_error)
            LogManager().log(
                self.tool_manager.logger_name,
                LogManagerThread.Level.ERROR,
                f"Post-processing error: {error_str}",
            )
            logger.end_execution(success=False, exit_code=str(post_error))
            raise

        finally:
            # Make sure to stop the PCM plugin and wait for it to clean up
            if pcm:
                pcm.stop()
                pcm.join(
                    timeout=5
                )  # Wait up to 5 seconds for PCM thread to finish
                LogManager().log(
                    self.tool_manager.logger_name,
                    LogManagerThread.Level.INFO,
                    "PCM monitoring stopped",
                )

        return exit_code
