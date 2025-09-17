#!/usr/bin/env python
# /****************************************************************************
# INTEL CONFIDENTIAL
# Copyright 2017-2024 Intel Corporation.
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
This module provides the implementation of a tool manager for the IMC tool.
"""
import argparse

from typing import List
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.utils.logging import Level
from scripts.libs.system_handler import SystemHandler
from scripts.libs.tools.imc.imc_parser import parse_args_list
from scripts.libs.tools.imc.imc_setup import verify_files
from scripts.libs.tools.imc.imc_process_results import process_results
from scripts.libs.definitions.errors import ErrorProvider
from scripts.libs.definitions.errors import (
    PROVIDER_NAMES,
    ErrorProviderNotFound,
)
from scripts.libs.errors.manager import ErrorManager
from scripts.libs.utils.logging import init_logging, Level
from scripts.libs.utils import stress
from scripts.libs.data_handlers.imc_data import ImcDataHandler
from scripts.libs.utils.environment import EnvironmentInfo
from scripts.libs.utils.structured_logger import StructuredLogger
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)
from scripts.libs.utils.memory_handler import MemoryHandler


class ImcToolManager:
    """
    A manager for IMC-specific operations.

    This class handles all IMC-specific logic including command generation,
    file verification, results processing, and error handling.

    Attributes:
        tool_data: The data handler containing IMC configuration and state.
        env_info: Dictionary containing IMC environment information
    """

    def __init__(self, args_string: str):
        """
        Initializes the IMC manager with the provided data handler.
        """
        self.TOOL_NAME = "Intelligent Memory Checker"
        self.tool_data = ImcDataHandler(
            parse_args_list(args_string),
        )

        self.logger_name = self.TOOL_NAME
        self.logger = StructuredLogger(logger_name="IMC")

    @classmethod
    def parse_args_list(cls, argv: List[str]) -> argparse.Namespace:
        return parse_args_list(argv)

    def generation_function(self, test_case, mem_per_instance, lpu):
        """
        Generates the command to be executed by the os system.
        """
        exec_path = [
            self.tool_data.parsed_args.imc_path,
            self.tool_data.parsed_args.xml_path,
        ]
        _cmd = []
        exec_path[1] = test_case
        _cmd.extend(exec_path)
        _cmd.extend(["-m", str(int(mem_per_instance))])
        if self.tool_data.parsed_args.blk_size:
            _cmd.extend(["-b", str(self.tool_data.parsed_args.blk_size)])
        if self.tool_data.parsed_args.time_to_execute:
            _cmd.extend(
                [
                    "--time_to_execute",
                    str(self.tool_data.parsed_args.time_to_execute),
                ]
            )

        _cmd = SystemHandler().os_system.generate_os_command(
            lpu, self.tool_data.parsed_args.priority, _cmd
        )

        if SystemHandler().os_system.platform_name == "svos":
            if self.tool_data.parsed_args.target:
                _cmd.extend(["-t", str(self.tool_data.parsed_args.target)])
        return _cmd

    def setup(self):
        """
        Review the paths corresponding to the IMC tool to check if the test cases and binary
        are valid.
        """
        self.logger_name = self.TOOL_NAME
        self.logger.log_setup(
            f"{self.TOOL_NAME} initialized with verbosity level {self.tool_data.parsed_args.verbosity}."
        )

        args = self.tool_data.parsed_args

        if isinstance(args.xml_path, list):
            test_count = len(args.xml_path)
            if test_count > 0:
                if test_count <= 5:
                    for idx, test_case in enumerate(args.xml_path):
                        self.logger.log_setup(f"Test Case {idx+1}: {test_case}")
                else:
                    for idx, test_case in enumerate(args.xml_path[:3]):
                        self.logger.log_setup(
                            f"  Test Case {idx+1}: {test_case}"
                        )
                    self.logger.log_setup(
                        f"  ... and {test_count-3} more test cases"
                    )
        else:
            self.logger.log_setup(f"Test Case: {args.xml_path}")

        self.logger.log_setup(f"IMC Binary Path: {args.imc_path}")

        self.logger.log_setup(f"Execution Type: {args.executionType}")

        if hasattr(args, "mem_use"):
            self.logger.log_setup(f"Memory Usage: {args.mem_use}")

        if hasattr(args, "blk_size") and args.blk_size is not None:
            self.logger.log_setup(f"Block Size: {args.blk_size} bytes")

        if hasattr(args, "timeout") and args.timeout != "0":
            self.logger.log_setup(f"Timeout: {args.timeout} minute(s)")
        else:
            self.logger.log_setup("Timeout: No timeout specified")

        if (
            hasattr(args, "time_to_execute")
            and args.time_to_execute is not None
        ):
            self.logger.log_setup(
                f"Execution Time: {args.time_to_execute} second(s)"
            )

        if hasattr(args, "lpus") and args.lpus:
            lpus_str = (
                ", ".join(map(str, args.lpus))
                if len(args.lpus) <= 10
                else f"{', '.join(map(str, args.lpus[:5]))} ... and {len(args.lpus)-5} more"
            )
            self.logger.log_setup(f"Logical Processors: {lpus_str}")

        if hasattr(args, "numa") and args.numa:
            numa_info = []
            for node, lpus in args.numa.items():
                lpus_str = (
                    ", ".join(map(str, lpus))
                    if len(lpus) <= 5
                    else f"{', '.join(map(str, lpus[:3]))} ... and {len(lpus)-3} more"
                )
                numa_info.append(f"Node {node}: {lpus_str}")
            self.logger.log_setup(f"NUMA Configuration: {'; '.join(numa_info)}")

        if hasattr(args, "priority"):
            self.logger.log_setup(f"Process Priority: {args.priority}")

        if hasattr(args, "stop_on_error"):
            self.logger.log_setup(
                f"Stop on Error: {'Yes' if args.stop_on_error else 'No'}"
            )

        if hasattr(args, "stress") and args.stress is not None:
            self.logger.log_setup(f"Stress Type: {args.stress}")

        if hasattr(args, "target") and args.target is not None:
            self.logger.log_setup(f"Target Path: {args.target}")

        # Initialize error manager
        self.mgr = ErrorManager(ErrorProvider.NoProvider)
        if self.tool_data.parsed_args.provider is ErrorProvider.Auto:
            for prov_name, prov_class in sorted(
                PROVIDER_NAMES.items(), reverse=True
            ):
                try:
                    self.mgr = ErrorManager(prov_class, False)
                    self.mgr.is_provider_set()
                    self.logger.log_debug(f"Error Provider set as: {prov_name}")
                    break
                except ErrorProviderNotFound:
                    pass
        if self.tool_data.parsed_args.provider not in (
            ErrorProvider.NoProvider,
            ErrorProvider.Auto,
        ):
            try:
                self.mgr = ErrorManager(self.tool_data.parsed_args.provider)
            except ErrorProviderNotFound as ex_err:
                self.logger.log_error(str(ex_err))
                LoggerManagerThread().pretty_exit(
                    self.logger_name, ExitCode.RUNNER_TOOL_FAILED
                )

        existing_err = self.mgr.get_errors()
        if existing_err:
            linefmt = "\n\t"
            existing_err_str = linefmt.join([str(err) for err in existing_err])
            self.logger.log_warning(
                f"Encountered error(s) before testing memory:{linefmt}{existing_err_str}"
            )
            self.mgr.clear_errors()

        self.mgr.mark_start()
        self.logger.log_setup("Setup completed successfully.")

    def initialize(self):
        """
        Initialize the IMC tool and log system memory information.
        This method logs all memory related information during the initialization phase.
        """
        MemoryHandler().log_memory_info(self.logger)

    def post_process(self):
        """
        Handle post-execution processing including error collection and result analysis.
        """
        if not self.logger:
            LoggerManager().create_logger(
                name="IMC", log_level=LoggerManagerThread.Level.INFO
            )

        try:

            results = self.tool_data.data["data_from_queue"]
            result_count = len(results)
            self.logger.log_post_execution(
                f"Retrieved {result_count} result entries from execution"
            )

            self.logger.log_post_execution("")

            self.logger.log_post_execution(
                "Checking for provider-detected errors..."
            )
            provider_errors_encountered = self.mgr.get_marked_errors()

            if provider_errors_encountered:
                error_count = len(provider_errors_encountered)
                self.logger.log_warning(
                    f"Found {error_count} provider-detected errors during execution"
                )

                max_errors_to_show = min(3, error_count)
                if max_errors_to_show > 0:
                    self.logger.log_warning(
                        f"Sample errors (showing {max_errors_to_show} of {error_count}):"
                    )
                    for i in range(max_errors_to_show):
                        self.logger.log_warning(
                            f"  - {str(provider_errors_encountered[i])}"
                        )
                    if error_count > max_errors_to_show:
                        self.logger.log_warning(
                            f"  ... and {error_count - max_errors_to_show} more"
                        )
            else:
                self.logger.log_post_execution(
                    "No provider-detected errors found"
                )

            self.logger.log_post_execution("")

            self.logger.log_post_execution(
                "Analyzing results and determining exit code..."
            )
            exit_code = process_results(results, provider_errors_encountered)

            if exit_code == ExitCode.OK:
                self.logger.log_post_execution(
                    "Post-processing completed successfully"
                )
            else:
                self.logger.log_warning(
                    f"Post-processing completed with errors: {exit_code} ({int(exit_code)})"
                )
                self.tool_data.data["execution_error"] = True

            ##After all post processing logs completed, stop all loggers
            LoggerManager().stop_all()
            LoggerManager().create_logger(
                name="IMC", log_level=LoggerManagerThread.Level.INFO
            )

            return int(exit_code)
        except Exception as e:
            self.logger.log_error(f"Error during post-processing: {str(e)}")
            return ExitCode.RUNNER_TOOL_FAILED
