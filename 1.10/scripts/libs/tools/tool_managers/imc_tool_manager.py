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
from scripts.libs.system_handler import SystemHandler
from scripts.libs.tools.imc.imc_parser import parse_args_list
from scripts.libs.tools.imc.imc_process_results import process_results
from scripts.libs.definitions.errors import ErrorProvider
from scripts.libs.definitions.errors import (
    PROVIDER_NAMES,
    ErrorProviderNotFound,
)
from scripts.libs.errors.manager import ErrorManager
from scripts.libs.data_handlers.imc_data import ImcDataHandler
from scripts.libs.loggers.phase_logger import PhaseLogger
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
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
        self.logger_name = "IMC"
        self.logger = PhaseLogger(logger_name=self.logger_name)

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

    def log_parameters(self):
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
            mem_str = str(args.mem_use).strip().rstrip("%")
            try:
                mem_pct = float(mem_str)
                mh = MemoryHandler()
                requested_bytes = int(mh.total_memory * (mem_pct / 100.0))

                instance_count = (
                    len(getattr(args, "lpus", []))
                    or sum(len(v) for v in getattr(args, "numa", {}).values())
                    or 1
                )
                per_instance_bytes = int(requested_bytes / instance_count)

                req_hr = mh.format_bytes(requested_bytes)
                total_hr = mh.format_bytes(mh.total_memory)
                per_instance_hr = mh.format_bytes(per_instance_bytes)

                self.logger.log_setup(
                    f"Requested memory Usage: {mem_pct}% (~{req_hr} of {total_hr}) | Per-instance: {per_instance_hr}"
                )
            except:
                self.logger.log_setup(f"Requested memory Usage: {args.mem_use}")
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

    def setup(self):
        """
        Review the paths corresponding to the IMC tool to check if the test cases and binary
        are valid.
        """
        self.tool_data.data["time_limit_reached"] = False
        self.tool_data.data["execution_completed"] = False
        self.logger.log_setup(
            f"{self.TOOL_NAME} initialized with verbosity level {self.tool_data.parsed_args.verbosity}."
        )
        self.log_parameters()
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
                self.mgr = ErrorManager(
                    self.tool_data.parsed_args.provider, False
                )
            except ErrorProviderNotFound as ex_err:
                self.logger.log_error(str(ex_err))
                LogManagerThread().pretty_exit(
                    self.logger_name, ExitCode.RUNNER_TOOL_FAILED
                )

        # Enable EDAC provider if selected
        if self.mgr._collection_method == ErrorProvider.EDAC:
            LogManager().enable_edac_provider()

        existing_err = self.mgr.get_errors()

        real_errors = []
        if existing_err:
            for err in existing_err:
                error_count = int(getattr(err, "count", 0))
                if error_count > 0:
                    real_errors.append(err)

        if real_errors:
            linefmt = "\n\t"
            existing_err_str = linefmt.join([str(err) for err in real_errors])
            self.logger.log_warning(
                f"Encountered error(s) before testing memory:{linefmt}{existing_err_str}"
            )
            self.mgr.clear_errors()
        else:
            self.logger.log_debug(
                "Memory error check completed - no existing errors found"
            )

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
            LogManager().create_logger(
                name=self.TOOL_NAME, log_level=LogManagerThread.Level.INFO
            )

        try:

            if self.tool_data.data.get("time_limit_reached", False):
                if not LogManager().manager_thread.has_logger(self.logger_name):
                    LogManager().create_logger(
                        name=self.logger_name,
                        log_level=LogManagerThread.Level.INFO,
                    )

            debug_log_file = LogManager().get_debug_log_file()
            if debug_log_file:
                self.logger.log_post_execution(
                    f"Complete debug logs have been written to: {debug_log_file}"
                )
                self.logger.log_post_execution(
                    "This file contains all detailed logs including those not shown in the terminal."
                )

            if self.tool_data.data.get("time_limit_reached", False) and hasattr(
                self.tool_data.parsed_args, "time_to_execute"
            ):
                self.logger.log_post_execution(
                    f"Processing results after time-based completion"
                )
            elif "execution_error" in self.tool_data.data:
                self.logger.log_post_execution(
                    "Processing results after execution error"
                )
            else:
                self.logger.log_post_execution(
                    "Processing execution results..."
                )

            results = self.tool_data.data["data_from_queue"]
            result_count = len(results)
            self.logger.log_post_execution(
                f"Retrieved {result_count} result entries from execution"
            )

            self.logger.log_post_execution("")

            memory_errors_detected = LogManager().has_memory_errors()
            if memory_errors_detected:
                LogManager().handle_emergency_memory_analysis()

                # Get memory error details from EDAC logger
                has_uncorrectable = False
                has_correctable = False
                thread_error_summary = {}

                try:
                    log_manager = LogManager()
                    edac_logger = log_manager.edac_logger
                    for (
                        thread_name,
                        thread_status,
                    ) in edac_logger.thread_error_status.items():
                        if (
                            thread_status.get("CE", 0) > 0
                            or thread_status.get("UE", 0) > 0
                        ):
                            thread_error_summary[thread_name] = thread_status
                            if thread_status.get("UE", 0) > 0:
                                has_uncorrectable = True
                            if thread_status.get("CE", 0) > 0:
                                has_correctable = True
                except (AttributeError, KeyError, TypeError) as e:
                    # Assume correctable errors if memory status check fails
                    self.logger.log_warning(
                        f"Memory check failed due to an exception: {str(e)}."
                    )
            else:
                self.logger.log_post_execution(
                    "No memory errors detected during execution"
                )

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
            if memory_errors_detected:
                # Get memory error details from EDAC logger
                has_uncorrectable = False
                has_correctable = False

                try:
                    log_manager = LogManager()
                    edac_logger = log_manager.edac_logger
                    for (
                        thread_status
                    ) in edac_logger.thread_error_status.values():
                        if thread_status.get("UE", 0) > 0:
                            has_uncorrectable = True
                        if thread_status.get("CE", 0) > 0:
                            has_correctable = True
                except (AttributeError, KeyError, TypeError) as e:
                    # Assume correctable errors if memory status check fails
                    has_correctable = True

                if has_uncorrectable:
                    if exit_code == ExitCode.OK:
                        exit_code = ExitCode.RUNNER_OS_ERR
                        self.logger.log_warning(
                            "Exit code changed to RUNNER_OS_ERR due to uncorrectable memory errors"
                        )
                    elif exit_code in (
                        ExitCode.RUNNER_TOOL_CORRUPTION,
                        ExitCode.SIGBUS,
                    ):
                        exit_code = ExitCode.RUNNER_OS_ERR_TOOL_CORRUPTION
                        self.logger.log_warning(
                            "Exit code changed to RUNNER_OS_ERR_TOOL_CORRUPTION due to tool errors with uncorrectable memory errors"
                        )
                    else:
                        exit_code = ExitCode.RUNNER_OS_ERR_TOOL_CORRUPTION
                        self.logger.log_warning(
                            "Exit code adjusted for uncorrectable memory errors detected during execution"
                        )
                elif has_correctable:
                    if exit_code == ExitCode.OK:
                        exit_code = ExitCode.RUNNER_OS_ERR
                        self.logger.log_warning(
                            "Exit code changed to RUNNER_OS_ERR due to correctable memory errors"
                        )

            if exit_code == ExitCode.OK:
                self.logger.log_post_execution(
                    "Post-processing completed successfully"
                )
            else:
                # Report different types of errors clearly
                error_description = "Unknown error"
                if memory_errors_detected:
                    if has_uncorrectable:
                        error_description = (
                            "Uncorrectable memory errors detected"
                        )
                    elif has_correctable:
                        error_description = "Correctable memory errors detected"

                    if "execution_error" in self.tool_data.data:
                        error_description += " + Tool execution errors"
                else:
                    error_description = "Tool execution errors"

                self.logger.log_warning(
                    f"Post-processing completed with errors: {error_description} (Exit Code: {int(exit_code)})"
                )
                self.tool_data.data["execution_error"] = True

            try:
                log_manager = LogManager()
                edac_logger = log_manager.edac_logger

                try:
                    edac_logger.log_memory_error_summary()
                except Exception as summary_error:
                    self.logger.log_warning(
                        f"Memory error summary failed: {str(summary_error)}"
                    )

                # Always generate memory diagnostics file
                edac_logger.log_memory_diagnostics()
                if getattr(edac_logger, "memory_provider", None):
                    self.logger.log_post_execution(
                        "Memory diagnostics file generated successfully"
                    )
            except Exception as diag_error:
                # Log warning if memory diagnostics generation fails
                self.logger.log_warning(
                    f"Failed to generate memory diagnostics: {str(diag_error)}"
                )

            ##After all post processing logs completed, stop all loggers
            LogManager().stop_all()
            LogManager().create_logger(
                name=self.TOOL_NAME, log_level=LogManagerThread.Level.INFO
            )

            return int(exit_code)
        except (AttributeError, ValueError, TypeError) as e:
            # Log error if post-processing fails due to data conversion or attribute issues
            self.logger.log_error(f"Error during post-processing: {str(e)}")
            return ExitCode.RUNNER_TOOL_FAILED
