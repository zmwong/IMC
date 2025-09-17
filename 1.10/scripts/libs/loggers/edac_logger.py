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
This module provides EDAC-specific logging functionality for memory error detection and reporting.
It handles all memory error diagnostics, thread association, and detailed error analysis.
"""
import copy
import logging
import os
from datetime import datetime
import time
from typing import Dict, List, Optional, Set
from scripts.libs.utils.lpu import expand_lpu_string
from scripts.libs.loggers.log_manager import LogManager, LogManagerThread
from scripts.libs.errors.providers.edac import EDACProvider


class EDACLogger:
    """
    A specialized logger for EDAC memory error detection and reporting.

    """

    def __init__(self, logger_name: str = "MEMORY"):
        """
        Initialize the EDAC logger.

        Args:
            logger_name (str): Name of the logger to use for output
        """
        self.logger_name = logger_name
        self.thread_memory_errors: Dict[str, List] = {}
        self.thread_error_status: Dict[str, Dict] = {}
        self.execution_start_time: Optional[float] = None
        self.baseline_error_signatures: Set[str] = set()
        self.baseline_error_counts: Dict[str, int] = {}
        self.registered_threads: Dict[str, int] = {}
        self.thread_lpu_mapping: Dict[str, int] = {}
        self.diagnostics_logged: bool = False
        self.summary_logged: bool = False
        self.execution_check_completed: bool = False
        self.post_execution_analyzed: bool = False

        self.memory_provider = None

    def enable_edac_provider(self):
        """Initialize EDAC provider when explicitly enabled."""
        if self.memory_provider is None:
            self.memory_provider = EDACProvider()
            self.memory_provider.init()

    def start_execution(self):
        """Mark the start of execution for memory error tracking"""
        self.execution_start_time = time.time()
        self.thread_memory_errors.clear()
        self.thread_error_status.clear()
        self.diagnostics_logged = False
        self.summary_logged = False
        self.execution_check_completed = False
        self.post_execution_analyzed = False
        self.baseline_error_counts = {}

        if self.memory_provider:
            try:
                initial_errors = self.memory_provider.get_errors()
                self.baseline_error_signatures.clear()
                self.baseline_error_counts.clear()

                for error in initial_errors:
                    location_signature = (
                        f"{error.mc}:{error.dimm_label}:{error.error_type}"
                    )
                    self.baseline_error_signatures.add(location_signature)

                    # Track baseline counts for comparison
                    self.baseline_error_counts[location_signature] = int(
                        error.count
                    )
                    baseline_thread = "PRE_EXECUTION_BASELINE"
                    if baseline_thread not in self.thread_memory_errors:
                        self.thread_memory_errors[baseline_thread] = []
                        self.thread_error_status[baseline_thread] = {
                            "CE": 0,
                            "UE": 0,
                            "status": "BASELINE",
                            "exit_code": 0,
                        }

                    self.thread_memory_errors[baseline_thread].append(error)

                    # Update baseline counters
                    error_type_str = str(error.error_type)
                    error_count = int(error.count)

                    if error_type_str == "Correctable":
                        self.thread_error_status[baseline_thread][
                            "CE"
                        ] += error_count
                    elif error_type_str == "Uncorrectable":
                        self.thread_error_status[baseline_thread][
                            "UE"
                        ] += error_count

            except (AttributeError, OSError) as e:
                # Log warning if baseline error check fails due to EDAC provider issues
                LogManager().log(
                    "MEMORY",
                    LogManagerThread.Level.WARNING,
                    f"Warning: Could not check baseline memory errors: {e}",
                )

    def register_thread(self, thread_name: str, pid: int, lpu: int = None):
        """

        This method establishes a mapping between execution threads and their system
        identifiers to enable accurate attribution of memory errors detected during
        execution. The registration creates internal tracking structures that are
        used by the error detection system to associate EDAC memory errors with
        specific execution threads based on memory controller locality and LPU
        assignment.

        Behavior:
            - Creates thread-to PID mapping for process identification
            - Establishes LPU to thread associations for CPU locality tracking
            - Initializes error tracking structures with baseline counters
            - Sets up thread status monitoring for exit code determination

        Args:
            thread_name (str): Unique identifier for the execution thread.
            pid (int): Process identifier of the thread as returned by the operating
                system
            lpu (int, optional): Logical Processing Unit number assigned to this
                thread

        Returns:
            None: This method performs registration operations and does not return
                any value. The registration state is maintained internally through
                instance attributes.

        """
        self.registered_threads[thread_name] = pid
        if lpu is not None:
            self.thread_lpu_mapping[thread_name] = lpu

        # Initialize thread error tracking
        if thread_name not in self.thread_error_status:
            self.thread_error_status[thread_name] = {
                "CE": 0,
                "UE": 0,
                "status": "REGISTERED",
                "exit_code": 0,
                "pid": pid,
                "registration_time": time.time(),
            }

    def unregister_thread(self, thread_name: str):
        """
        Unregister a thread from error tracking.

        Args:
            thread_name (str): Name of the thread to unregister
        """
        if thread_name in self.registered_threads:
            del self.registered_threads[thread_name]
        if thread_name in self.thread_lpu_mapping:
            del self.thread_lpu_mapping[thread_name]

    def _extract_lpu_from_command(self, cmd_args):
        """
        This method parses command line arguments to identify which logical processing units
        should be used for execution. It supports multiple command patterns commonly
        used in IMC memory validation workflows for CPU binding and affinity control.

        Behaviour
            - numactl --physcpubind= syntax for NUMA aware CPU binding
            - taskset -c syntax for CPU affinity specification
            - Single LPU values, ranges, and comma-separated lists
            - Validates extracted values using the LPU utility functions


        Args:
            cmd_args (list): List of command-line arguments to parse. Each element
                should be a string representing a command argument.

        Returns:
            int or None: The first valid LPU number extracted from the command
                arguments. Returns None if no valid LPU specification is found,
                if the argument list is empty/None, or if parsing fails.

        """
        if not cmd_args:
            return None

        try:
            for i, arg in enumerate(cmd_args):
                lpu_value = None

                if arg.startswith("--physcpubind="):
                    lpu_value = arg.split("=", 1)[1]
                elif (
                    arg == "taskset"
                    and i + 2 < len(cmd_args)
                    and cmd_args[i + 1] == "-c"
                ):
                    lpu_value = cmd_args[i + 2]

                if lpu_value:
                    validated_lpus = expand_lpu_string(lpu_value)
                    return validated_lpus[0] if validated_lpus else None

        except (ValueError, IndexError, AttributeError, TypeError):
            pass

        return None

    def get_thread_memory_status(self, thread_name: str) -> Dict:
        """
        Get memory error status for a specific thread.

        Args:
            thread_name (str): Name of the thread

        Returns:
            dict: Status with CE/UE counts and exit code
        """
        return self.thread_error_status.get(
            thread_name, {"CE": 0, "UE": 0, "status": "OK", "exit_code": 0}
        )

    def _determine_error_thread(self, error):
        """
        Determine which IMC thread should be associated with a memory error.
        Uses error location and registered threads for accurate mapping.

        Args:
            error: EDACErrorEntry with memory error details

        Returns:
            str: Thread name to associate with this error
        """
        try:
            # Check if error has a thread_id that we've registered
            if hasattr(error, "thread_id") and error.thread_id:
                if error.thread_id in self.registered_threads:
                    return error.thread_id

            # Use registered threads for mapping
            if self.registered_threads:
                registered_thread_names = list(self.registered_threads.keys())
                try:
                    mc_id = int(getattr(error, "mc", 0))
                    thread_index = mc_id % len(registered_thread_names)
                    return registered_thread_names[thread_index]
                except (ValueError, TypeError):
                    return registered_thread_names[0]

            # Check LogManager thread logs if available
            active_threads = (
                list(LogManager().thread_logs.keys())
                if hasattr(LogManager(), "thread_logs")
                and LogManager().thread_logs
                else []
            )

            if active_threads:
                try:
                    mc_id = int(getattr(error, "mc", 0))
                    thread_index = mc_id % len(active_threads)
                    return active_threads[thread_index]
                except (ValueError, TypeError):
                    return active_threads[0]

            return "PRE_EXECUTION_BASELINE"

        except (AttributeError, TypeError, ValueError) as e:
            return "PRE_EXECUTION_BASELINE"

    def get_thread_exit_code(self, thread_name: str) -> int:
        """
        Get the appropriate exit code for a thread based on memory errors detected.

        Args:
            thread_name (str): Name of the thread

        Returns:
            int: Exit code (0 for success, 1 for correctable errors, 2 for uncorrectable errors)
        """
        if thread_name in self.thread_error_status:
            status = self.thread_error_status[thread_name]
            if status.get("UE", 0) > 0:
                return 2
            elif status.get("CE", 0) > 0:
                return 1
        return 0  # Success - no memory errors

    def has_thread_memory_errors(self, thread_name: str) -> bool:
        """
        Check if a specific thread has memory errors.

        Args:
            thread_name (str): Name of the thread to check

        Returns:
            bool: True if the thread has memory errors
        """
        if thread_name not in self.thread_error_status:
            return False
        status = self.thread_error_status[thread_name]
        return status.get("CE", 0) > 0 or status.get("UE", 0) > 0

    def quick_memory_check(self, thread_name: Optional[str] = None):
        """
        Simple memory error check.
        """
        if not self.memory_provider or not thread_name:
            return

        try:
            if thread_name not in self.thread_memory_errors:
                self.thread_memory_errors[thread_name] = []
                self.thread_error_status[thread_name] = {
                    "CE": 0,
                    "UE": 0,
                    "status": "OK",
                    "exit_code": 0,
                }

        except (AttributeError, ValueError, TypeError) as e:
            # Log warning if memory error checking fails due to EDAC provider issues
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.DEBUG,
                f"Failed to initialize thread tracking for {thread_name}: {e}",
            )

    def check_and_log_memory_errors(self, force_recheck: bool = False):
        """
        Post-execution memory error check

        Args:
            force_recheck: If True, bypasses the duplicate analysis prevention
        """
        if not self.memory_provider:
            return

        if self.post_execution_analyzed and not force_recheck:
            return

        if not force_recheck:
            self.post_execution_analyzed = True

        try:
            current_errors = self.memory_provider.get_errors()
            if not current_errors:
                return

            for error in current_errors:
                location_signature = (
                    f"{error.mc}:{error.dimm_label}:{error.error_type}"
                )
                current_count = int(error.count)
                is_new_error = False
                new_error_count = 0

                if location_signature in self.baseline_error_signatures:
                    baseline_count = self.baseline_error_counts.get(
                        location_signature, 0
                    )
                    if current_count > baseline_count:
                        is_new_error = True
                        new_error_count = current_count - baseline_count
                else:
                    is_new_error = True
                    new_error_count = current_count

                if is_new_error and new_error_count > 0:
                    responsible_thread = self._determine_error_thread(error)

                    if responsible_thread != "PRE_EXECUTION_BASELINE":
                        # Check if we've already processed this exact error to avoid duplicates
                        error_already_processed = False
                        if responsible_thread in self.thread_memory_errors:
                            for existing_error in self.thread_memory_errors[
                                responsible_thread
                            ]:
                                existing_sig = f"{existing_error.mc}:{existing_error.dimm_label}:{existing_error.error_type}"
                                if existing_sig == location_signature:
                                    error_already_processed = True
                                    break

                        if not error_already_processed:
                            if (
                                responsible_thread
                                not in self.thread_memory_errors
                            ):
                                self.thread_memory_errors[
                                    responsible_thread
                                ] = []
                                self.thread_error_status[responsible_thread] = {
                                    "CE": 0,
                                    "UE": 0,
                                    "status": "OK",
                                    "exit_code": 0,
                                }
                            # Create a copy to avoid reference issues and only register the new ones
                            new_error = copy.copy(error)
                            new_error.count = new_error_count

                            self.thread_memory_errors[
                                responsible_thread
                            ].append(new_error)

                            # Update status with only new error counts
                            error_type_str = str(error.error_type)

                            if error_type_str == "Correctable":
                                self.thread_error_status[responsible_thread][
                                    "CE"
                                ] += new_error_count
                                self.thread_error_status[responsible_thread][
                                    "status"
                                ] = "WARNING"
                                self.thread_error_status[responsible_thread][
                                    "exit_code"
                                ] = 1
                            elif error_type_str == "Uncorrectable":
                                self.thread_error_status[responsible_thread][
                                    "UE"
                                ] += new_error_count
                                self.thread_error_status[responsible_thread][
                                    "status"
                                ] = "CRITICAL"
                                self.thread_error_status[responsible_thread][
                                    "exit_code"
                                ] = 2

        except (AttributeError, ValueError, TypeError) as e:
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.DEBUG,
                f"Memory error attribution failed: {e}",
            )

    def immediate_post_execution_check(self) -> bool:
        """
        The method ensures that post execution analysis is performed only once per
        execution cycle to prevent duplicate error reporting and maintains thread
        safety through execution state tracking.

        Behavior:
            - Scans all EDAC error sources for new memory errors
            - Compares current error counts against baseline measurements
            - Associates detected errors with appropriate execution threads
            - Updates thread error status with CE/UE counts and exit codes
            - Skips analysis if memory provider is unavailable or check already completed

        Args:
            None: This method takes no parameters.

        Returns:
            bool: True if any memory errors were detected during execution
                  across any thread

        Raises:
            Exception:
                - AttributeError: If EDAC provider attributes are missing
                - OSError: If EDAC sysfs files are inaccessible
                - ValueError: If error count parsing fails

        """
        if not self.memory_provider or self.execution_check_completed:
            return False

        self.execution_check_completed = True

        try:
            # Scan for memory errors
            self.check_and_log_memory_errors()

            for thread_name, status in self.thread_error_status.items():
                if thread_name != "PRE_EXECUTION_BASELINE":
                    if status.get("CE", 0) > 0 or status.get("UE", 0) > 0:
                        return True
            return False

        except Exception as e:
            LogManager().log(
                "MEMORY",
                LogManagerThread.Level.ERROR,
                f"Post-execution error check failed: {e}",
            )
            return False

    def has_memory_errors(self) -> bool:
        """
        Check if any memory errors were detected during execution.

        Returns:
            bool: True if any memory errors were found
        """
        return bool(
            self.thread_memory_errors
            or any(
                status.get("CE", 0) > 0 or status.get("UE", 0) > 0
                for status in self.thread_error_status.values()
                if isinstance(status, dict)
            )
        )

    def _map_edac_thread_to_execution_thread(self, edac_thread_id: str) -> str:
        """
        Simple thread mapping using registered threads first, then LogManager fallback.
        """
        if self.registered_threads:
            registered_thread_names = list(self.registered_threads.keys())
            return registered_thread_names[0]

        active_threads = (
            list(LogManager().thread_logs.keys())
            if LogManager().thread_logs
            else []
        )

        if not active_threads:
            return edac_thread_id

        # Map to first available thread
        return active_threads[0]

    def log_memory_diagnostics(self):
        """
        Generate memory diagnostics file. Only one file per execution.
        """
        if self.diagnostics_logged:
            return

        if not self.memory_provider:
            LogManager().log(
                "SYS",
                LogManagerThread.Level.INFO,
                "Memory diagnostics file not generated: No error provider detected.",
            )
            return

        try:
            self.diagnostics_logged = True

            if (
                not self.thread_memory_errors
                and not self.post_execution_analyzed
            ):
                self.check_and_log_memory_errors(force_recheck=True)

            log_dir = LogManager().get_execution_log_dir()
            os.makedirs(log_dir, exist_ok=True)

            memory_diagnostics_file = os.path.join(
                log_dir, "memory_diagnostics.log"
            )

            self.logger_name = "MEMORY"

            LogManager().create_logger(
                name=self.logger_name,
                log_level=LogManagerThread.Level.DEBUG,
                log_format=logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "%Y-%m-%d %H:%M:%S",
                ),
            )

            memory_logger = (
                LogManager()
                .manager_thread.loggers.get(self.logger_name, {})
                .get("logger")
            )
            if not memory_logger:
                return

            file_handler = logging.FileHandler(memory_diagnostics_file)
            file_handler.setLevel(LogManagerThread.Level.DEBUG)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "%Y-%m-%d %H:%M:%S",
                )
            )

            memory_logger.propagate = False
            for handler in memory_logger.handlers[:]:
                memory_logger.removeHandler(handler)
            memory_logger.addHandler(file_handler)

            self._log_diagnostics_header()

            if self.thread_memory_errors or self.thread_error_status:
                analysis_data = self._analyze_thread_memory_errors()
                self._log_system_overview(analysis_data)
                self._log_error_summary(analysis_data)
                self._log_memory_topology(analysis_data)
                self._log_thread_analysis()
            else:
                self.log(
                    self.logger_name,
                    LogManagerThread.Level.INFO,
                    "No memory errors detected",
                )

            self._log_diagnostics_footer()

            LogManager().manager_thread._process_log_queue(flush_all=True)

        except (OSError, IOError, PermissionError) as e:
            # Log error if memory diagnostics file creation fails
            LogManager().log(
                "SYS",
                LogManagerThread.Level.ERROR,
                f"Memory diagnostics failed: {str(e)}",
            )

    def log(self, logger_name: str, level: int, msg: str):
        """Helper method to log messages using LogManager"""
        from scripts.libs.loggers.log_manager import LogManager

        LogManager().log(logger_name, level, msg)

    def log_memory_error_summary(self):
        """
        Log a comprehensive summary of memory errors detected during execution,
        including specific thread failure information for IMC logs.
        """

        if self.summary_logged:
            return

        self.summary_logged = True

        if not self.thread_memory_errors and not self.thread_error_status:
            LogManager().log(
                "SYS",
                LogManagerThread.Level.INFO,
                "No memory errors detected during execution",
            )
            return

        execution_threads_with_errors = []
        total_execution_errors = 0

        for thread_name, status in self.thread_error_status.items():
            thread_ce = status.get("CE", 0)
            thread_ue = status.get("UE", 0)
            total_thread_errors = thread_ce + thread_ue

            if total_thread_errors > 0:
                total_execution_errors += total_thread_errors

                # Get PID if available
                pid_info = ""
                if thread_name in self.registered_threads:
                    pid_info = f" (PID: {self.registered_threads[thread_name]})"

                execution_threads_with_errors.append(
                    {
                        "name": thread_name,
                        "pid_info": pid_info,
                        "ce": thread_ce,
                        "ue": thread_ue,
                        "total": total_thread_errors,
                        "exit_code": status.get("exit_code", 0),
                    }
                )

        # Log comprehensive execution summary
        LogManager().log("SYS", LogManagerThread.Level.INFO, "")
        LogManager().log(
            "SYS",
            LogManagerThread.Level.INFO,
            "=" * 80,
        )
        LogManager().log(
            "SYS",
            LogManagerThread.Level.INFO,
            "MEMORY ERROR EXECUTION SUMMARY",
        )
        LogManager().log(
            "SYS",
            LogManagerThread.Level.INFO,
            "=" * 80,
        )

        if total_execution_errors > 0:
            # Log overall summary
            LogManager().log(
                "SYS",
                LogManagerThread.Level.WARNING,
                f"NEW ERRORS DURING EXECUTION: {total_execution_errors} errors across {len(execution_threads_with_errors)} thread(s)",
            )
            LogManager().log("SYS", LogManagerThread.Level.INFO, "")
            LogManager().log(
                "SYS",
                LogManagerThread.Level.WARNING,
                "THREADS WITH MEMORY ERRORS:",
            )

            # Log details for each failed thread
            for thread_info in execution_threads_with_errors:
                thread_status = "FAILED"
                if thread_info["ue"] > 0:
                    thread_status = "CRITICAL"
                elif thread_info["ce"] > 0:
                    thread_status = "WARNING"

                LogManager().log(
                    "SYS",
                    LogManagerThread.Level.WARNING,
                    f"    {thread_info['name']}{thread_info['pid_info']}: {thread_status}",
                )
                LogManager().log(
                    "SYS",
                    LogManagerThread.Level.INFO,
                    f"     CE: {thread_info['ce']}, UE: {thread_info['ue']}, Exit Code: {thread_info['exit_code']}",
                )

    def _log_diagnostics_header(self):
        """Log comprehensive system header information"""
        import os

        self.log(self.logger_name, LogManagerThread.Level.INFO, "")
        self.log(
            self.logger_name, LogManagerThread.Level.INFO, "╔" + "═" * 78 + "╗"
        )
        self.log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "║" + " " * 22 + " MEMORY VALIDATION DIAGNOSTICS" + " " * 26 + "║",
        )
        self.log(
            self.logger_name, LogManagerThread.Level.INFO, "╚" + "═" * 78 + "╝"
        )
        self.log(self.logger_name, LogManagerThread.Level.INFO, "")

        self.log(
            self.logger_name, LogManagerThread.Level.INFO, " SYSTEM INFORMATION"
        )
        self.log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "---Kernel Version: " + str(os.uname().release),
        )
        self.log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "---Hostname: " + str(os.uname().nodename),
        )
        self.log(self.logger_name, LogManagerThread.Level.INFO, "")

    def _get_edac_data(self):
        """Get EDAC provider and error data"""
        if not self.memory_provider:
            return None, []

        try:
            edac_errors = self.memory_provider.get_errors()
            return self.memory_provider, edac_errors
        except (AttributeError, OSError) as e:
            # Return empty error list if EDAC provider fails
            return self.memory_provider, []

    def _analyze_thread_memory_errors(self) -> Dict:
        """
        Analyze memory errors from processed thread data.

        Returns:
            dict: Analysis results with statistics and categorizations
        """
        analysis = {
            "total_error_entries": 0,
            "total_error_count": 0,
            "correctable_errors": 0,
            "uncorrectable_errors": 0,
            "affected_dimms": set(),
            "affected_controllers": set(),
            "thread_distribution": {},
            "dimm_error_map": {},
            "severity_assessment": "OK",
        }

        for thread_name, errors in self.thread_memory_errors.items():
            if thread_name == "PRE_EXECUTION_BASELINE":
                continue

            for error in errors:
                error_count = int(error.count)
                analysis["total_error_entries"] += 1
                analysis["total_error_count"] += error_count

                if str(error.error_type) == "Correctable":
                    analysis["correctable_errors"] += error_count
                elif str(error.error_type) == "Uncorrectable":
                    analysis["uncorrectable_errors"] += error_count

                analysis["affected_dimms"].add(error.dimm_label)
                analysis["affected_controllers"].add(f"MC{error.mc}")

                # Thread distribution
                if thread_name not in analysis["thread_distribution"]:
                    analysis["thread_distribution"][thread_name] = {
                        "CE": 0,
                        "UE": 0,
                        "errors": [],
                    }

                if str(error.error_type) == "Correctable":
                    analysis["thread_distribution"][thread_name][
                        "CE"
                    ] += error_count
                elif str(error.error_type) == "Uncorrectable":
                    analysis["thread_distribution"][thread_name][
                        "UE"
                    ] += error_count

                analysis["thread_distribution"][thread_name]["errors"].append(
                    error
                )

                # DIMM error mapping
                if error.dimm_label not in analysis["dimm_error_map"]:
                    analysis["dimm_error_map"][error.dimm_label] = {
                        "CE": 0,
                        "UE": 0,
                        "errors": [],
                    }

                if str(error.error_type) == "Correctable":
                    analysis["dimm_error_map"][error.dimm_label][
                        "CE"
                    ] += error_count
                elif str(error.error_type) == "Uncorrectable":
                    analysis["dimm_error_map"][error.dimm_label][
                        "UE"
                    ] += error_count

                analysis["dimm_error_map"][error.dimm_label]["errors"].append(
                    error
                )

        # Determine overall severity
        if analysis["uncorrectable_errors"] > 0:
            analysis["severity_assessment"] = "CRITICAL"
        elif analysis["correctable_errors"] > 0:
            analysis["severity_assessment"] = "WARNING"

        return analysis

    def _analyze_memory_errors(self, edac_errors: List) -> Dict:
        """
        Analyze memory errors and generate comprehensive statistics.

        Args:
            edac_errors: List of EDAC error entries

        Returns:
            dict: Analysis results with statistics and categorizations
        """
        analysis = {
            "total_error_entries": len(edac_errors),
            "total_error_count": 0,
            "correctable_errors": 0,
            "uncorrectable_errors": 0,
            "affected_dimms": set(),
            "affected_controllers": set(),
            "thread_distribution": {},
            "dimm_error_map": {},
            "severity_assessment": "OK",
        }

        for error in edac_errors:
            error_count = int(error.count)
            analysis["total_error_count"] += error_count

            if str(error.error_type) == "Correctable":
                analysis["correctable_errors"] += error_count
            elif str(error.error_type) == "Uncorrectable":
                analysis["uncorrectable_errors"] += error_count

            analysis["affected_dimms"].add(error.dimm_label)
            analysis["affected_controllers"].add(f"MC{error.mc}")

            # Thread distribution
            thread_id = getattr(error, "thread_id", "Unknown")
            mapped_thread = self._map_edac_thread_to_execution_thread(thread_id)

            if mapped_thread not in analysis["thread_distribution"]:
                analysis["thread_distribution"][mapped_thread] = {
                    "CE": 0,
                    "UE": 0,
                    "errors": [],
                }

            if str(error.error_type) == "Correctable":
                analysis["thread_distribution"][mapped_thread][
                    "CE"
                ] += error_count
            elif str(error.error_type) == "Uncorrectable":
                analysis["thread_distribution"][mapped_thread][
                    "UE"
                ] += error_count

            analysis["thread_distribution"][mapped_thread]["errors"].append(
                error
            )

            # DIMM error mapping
            if error.dimm_label not in analysis["dimm_error_map"]:
                analysis["dimm_error_map"][error.dimm_label] = {
                    "CE": 0,
                    "UE": 0,
                    "errors": [],
                }

            if str(error.error_type) == "Correctable":
                analysis["dimm_error_map"][error.dimm_label][
                    "CE"
                ] += error_count
            elif str(error.error_type) == "Uncorrectable":
                analysis["dimm_error_map"][error.dimm_label][
                    "UE"
                ] += error_count

            analysis["dimm_error_map"][error.dimm_label]["errors"].append(error)

        # Determine overall severity
        if analysis["uncorrectable_errors"] > 0:
            analysis["severity_assessment"] = "CRITICAL"
        elif analysis["correctable_errors"] > 0:
            analysis["severity_assessment"] = "WARNING"

        return analysis

    def _log_system_overview(self, analysis: Dict):
        """Log system overview section"""
        from scripts.libs.loggers.log_manager import LogManager

        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "┌" + "─" * 78 + "┐"
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "│ SYSTEM OVERVIEW" + " " * 61 + " │",
        )
        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "└" + "─" * 78 + "┘"
        )

        # Overall status
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"Overall Status: {analysis['severity_assessment']}",
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"Total Error Count: {analysis['total_error_count']:,} errors",
        )

        # Hardware summary
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"Memory Controllers Affected: {len(analysis['affected_controllers'])}",
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"DIMMs with Errors: {len(analysis['affected_dimms'])}",
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"Threads with Memory Errors: {len(analysis['thread_distribution'])}",
        )

    def _log_error_summary(self, analysis: Dict):
        """Log error summary section"""
        from scripts.libs.loggers.log_manager import LogManager

        LogManager().log(self.logger_name, LogManagerThread.Level.INFO, "")
        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "┌" + "─" * 78 + "┐"
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "│ ERROR SUMMARY" + " " * 63 + " │",
        )
        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "└" + "─" * 78 + "┘"
        )

        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"Total Memory Errors Detected: {analysis['total_error_count']:,}",
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"  Correctable Errors (CE): {analysis['correctable_errors']:,}",
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            f"  Uncorrectable Errors (UE): {analysis['uncorrectable_errors']:,}",
        )

    def _log_memory_topology(self, analysis: Dict):
        """Log memory topology and error distribution"""
        from scripts.libs.loggers.log_manager import LogManager

        LogManager().log(self.logger_name, LogManagerThread.Level.INFO, "")
        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "┌" + "─" * 78 + "┐"
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "│ MEMORY TOPOLOGY & ERROR DISTRIBUTION" + " " * 39 + " │",
        )
        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "└" + "─" * 78 + "┘"
        )

        for dimm_label, dimm_data in sorted(analysis["dimm_error_map"].items()):
            total_dimm_errors = dimm_data["CE"] + dimm_data["UE"]

            LogManager().log(self.logger_name, LogManagerThread.Level.INFO, "")
            LogManager().log(
                self.logger_name, LogManagerThread.Level.INFO, f"{dimm_label}"
            )
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.INFO,
                f"   Total Errors: {total_dimm_errors:,} (CE: {dimm_data['CE']:,}, UE: {dimm_data['UE']:,})",
            )

            # Show sample errors for this DIMM
            sample_errors = dimm_data["errors"][:2]
            for error in sample_errors:
                error_details = []
                if hasattr(error, "row") and error.row:
                    error_details.append(f"Row: {error.row}")
                if hasattr(error, "column") and error.column:
                    error_details.append(f"Col: {error.column}")
                if hasattr(error, "bank") and error.bank:
                    error_details.append(f"Bank: {error.bank}")

                detail_str = (
                    f" ({', '.join(error_details)})" if error_details else ""
                )
                LogManager().log(
                    self.logger_name,
                    LogManagerThread.Level.INFO,
                    f"      {error.error_type}: {error.count} error(s){detail_str}",
                )

    def _log_thread_analysis(self):
        """Log thread-based error analysis showing which execution threads failed"""

        LogManager().log(self.logger_name, LogManagerThread.Level.INFO, "")
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "DETAILED THREAD-BASED ERROR ANALYSIS",
        )
        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "=" * 80
        )

        for thread_name, thread_status in sorted(
            self.thread_error_status.items()
        ):
            ce_count = thread_status.get("CE", 0)
            ue_count = thread_status.get("UE", 0)
            total_errors = ce_count + ue_count

            # Only show threads that have errors
            if total_errors == 0:
                continue

            # Create thread header with LPU information if available
            lpu_info = ""
            if thread_name in self.thread_lpu_mapping:
                lpu_info = f" (LPU: {self.thread_lpu_mapping[thread_name]})"

            header_text = f"THREAD {thread_name}{lpu_info} - Total Error Count: {total_errors:,}"

            LogManager().log(self.logger_name, LogManagerThread.Level.INFO, "")
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.INFO,
                "┌" + "─" * 78 + "┐",
            )
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.INFO,
                f"│ {header_text:<76} │",
            )
            LogManager().log(
                self.logger_name,
                LogManagerThread.Level.INFO,
                "└" + "─" * 78 + "┘",
            )

            if thread_name in self.registered_threads:
                pid = self.registered_threads[thread_name]
                lpu_text = ""
                if thread_name in self.thread_lpu_mapping:
                    lpu_text = f", LPU: {self.thread_lpu_mapping[thread_name]}"
                LogManager().log(
                    self.logger_name,
                    LogManagerThread.Level.INFO,
                    f"   Thread PID: {pid}{lpu_text}",
                )

            if thread_name in self.thread_memory_errors:
                errors = self.thread_memory_errors[thread_name]

                thread_dimm_map = {}
                for error in errors:
                    thread_dimm_map.setdefault(error.dimm_label, []).append(
                        error
                    )

                for dimm_label, dimm_errors in thread_dimm_map.items():
                    LogManager().log(
                        self.logger_name, LogManagerThread.Level.INFO, ""
                    )
                    LogManager().log(
                        self.logger_name,
                        LogManagerThread.Level.INFO,
                        f"   DIMM: {dimm_label}",
                    )
                    LogManager().log(
                        self.logger_name,
                        LogManagerThread.Level.INFO,
                        "   " + "─" * 70,
                    )

                    for error in dimm_errors:
                        error_prefix = (
                            "[CRITICAL-UE]"
                            if str(error.error_type) == "Uncorrectable"
                            else " [WARNING-CE]"
                        )
                        LogManager().log(
                            self.logger_name,
                            LogManagerThread.Level.INFO,
                            f"   {error_prefix} Error Details:",
                        )
                        LogManager().log(
                            self.logger_name,
                            LogManagerThread.Level.INFO,
                            f"      Error Type: {error.error_type}",
                        )
                        LogManager().log(
                            self.logger_name,
                            LogManagerThread.Level.INFO,
                            f"      Count: {int(error.count):,}",
                        )
                        LogManager().log(
                            self.logger_name,
                            LogManagerThread.Level.INFO,
                            f"      Memory Controller: MC{error.mc}",
                        )
                        LogManager().log(
                            self.logger_name,
                            LogManagerThread.Level.INFO,
                            f"      Chip Select: {error.chip_select}",
                        )
                        if error.socket is not None:
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Socket: {error.socket}",
                            )
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Channel: {error.channel}",
                            )
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Slot: {error.slot}",
                            )

                        # Physical Memory Address Information
                        if hasattr(error, "page") and error.page:
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Page Address: {error.page}",
                            )
                        if (
                            hasattr(error, "system_address")
                            and error.system_address
                        ):
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Physical Address: {error.system_address}",
                            )

                        # Virtual Memory Address Information
                        if (
                            hasattr(error, "virtual_address")
                            and error.virtual_address
                        ):
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Virtual Address: {error.virtual_address}",
                            )

                        # Memory Topology Details
                        if hasattr(error, "row") and error.row:
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Row: 0x{int(error.row):X} ({error.row})",
                            )
                        if hasattr(error, "column") and error.column:
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Column: 0x{int(error.column):X} ({error.column})",
                            )
                        if hasattr(error, "bank") and error.bank:
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Bank: 0x{int(error.bank):X} ({error.bank})",
                            )
                        if hasattr(error, "bank_group") and error.bank_group:
                            LogManager().log(
                                self.logger_name,
                                LogManagerThread.Level.INFO,
                                f"      Bank Group: 0x{int(error.bank_group):X} ({error.bank_group})",
                            )
                        LogManager().log(
                            self.logger_name, LogManagerThread.Level.INFO, ""
                        )

    def _log_diagnostics_footer(self):
        """Log the diagnostics footer"""
        from scripts.libs.loggers.log_manager import LogManager

        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "=" * 80
        )
        LogManager().log(
            self.logger_name,
            LogManagerThread.Level.INFO,
            "END OF MEMORY DIAGNOSTICS REPORT",
        )
        LogManager().log(
            self.logger_name, LogManagerThread.Level.INFO, "=" * 80
        )
        LogManager().log(self.logger_name, LogManagerThread.Level.INFO, "")
