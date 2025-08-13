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
"""
This module enhances the LoggerManager with structured logging capabilities
"""

import time
import platform
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)
from scripts.libs.definitions import exit_codes


class StructuredLogger:
    """
    A wrapper around LoggerManager to provide structured logging with clear
    phases and visual separation.
    """

    # ANSI color codes for terminal
    COLORS = {
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
        "BLUE": "\033[94m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
        "MAGENTA": "\033[95m",
        "CYAN": "\033[96m",
    }

    EXECUTION_PHASES = {
        "HEADER": {"color": "CYAN", "symbol": "="},
        "INITIALIZATION": {"color": "GREEN", "symbol": "-"},
        "SETUP": {"color": "BLUE", "symbol": "-"},
        "EXECUTION": {"color": "MAGENTA", "symbol": "-"},
        "POST_EXECUTION": {"color": "YELLOW", "symbol": "-"},
    }

    COLOR_PREFIXES = {
        "INIT": None,
        "SETUP": None,
        "EXEC": None,
        "POST": None,
        "ERROR": None,
    }

    SEPARATOR_LENGTH = 80

    def __init__(self, logger_name="IMC", version=f"1.9"):
        """
        Initialize the StructuredLogger with the specified logger name.

        Args:
            logger_name (str): The name of the logger to use
            version (str): The version of the IMC tool
        """
        self.logger_name = logger_name
        self.version = version
        self.start_time = None
        self.phase_times = {}

        self._separator_cache = {}

        init_color = self.COLORS.get(
            self.EXECUTION_PHASES["INITIALIZATION"]["color"], ""
        )
        setup_color = self.COLORS.get(
            self.EXECUTION_PHASES["SETUP"]["color"], ""
        )
        exec_color = self.COLORS.get(
            self.EXECUTION_PHASES["EXECUTION"]["color"], ""
        )
        post_color = self.COLORS.get(
            self.EXECUTION_PHASES["POST_EXECUTION"]["color"], ""
        )
        reset = self.COLORS["RESET"]

        self.COLOR_PREFIXES = {
            "INIT": f"{init_color}[INIT]{reset} ",
            "SETUP": f"{setup_color}[SETUP]{reset} ",
            "EXEC": f"{exec_color}[EXEC]{reset} ",
            "POST": f"{post_color}[POST]{reset} ",
            "ERROR": f"{self.COLORS['RED']}[ERROR]{reset} ",
            "TIMEOUT": f"{self.COLORS['YELLOW']}[TIMEOUT]{reset} ",
        }

        self._detailed_logging = False

    def _get_separator(self, phase):
        """
        Generate a separator line for the specified phase.

        Args:
            phase (str): The execution phase name

        Returns:
            str: A formatted separator string
        """
        cache_key = phase
        if cache_key in self._separator_cache:
            return self._separator_cache[cache_key]

        phase_config = self.EXECUTION_PHASES.get(
            phase, self.EXECUTION_PHASES["HEADER"]
        )
        color = self.COLORS.get(phase_config["color"], "")
        symbol = phase_config["symbol"]

        text = f" {phase} "
        padding_length = self.SEPARATOR_LENGTH - len(text)
        left_padding = symbol * (padding_length // 2)
        right_padding = symbol * (padding_length - len(left_padding))

        separator = f"{color}{left_padding}{self.COLORS['BOLD']}{text}{self.COLORS['RESET']}{color}{right_padding}{self.COLORS['RESET']}"

        self._separator_cache[cache_key] = separator
        return separator

    def _get_system_info(self):
        """
        Get formatted system information for log headers.

        Returns:
            str: Formatted system information
        """
        return (
            f"System: {platform.system()} {platform.release()} | "
            f"Python: {platform.python_version()} | "
            f"IMC Version: {self.version} "
        )

    def _log_with_level(self, level, message):
        """
        Log a message with the specified level.

        Args:
            level (int): The logging level
            message (str): The message to log
        """
        LoggerManager().log(self.logger_name, level, message)

    def start_execution(self):
        """
        Log the start of execution with a header containing system information.
        """
        self.start_time = time.time()

        self._log_with_level(LoggerManagerThread.Level.INFO, "")
        header = self._get_separator("SYS_INFO")
        self._log_with_level(LoggerManagerThread.Level.INFO, header)

        system_info = self._get_system_info()
        self._log_with_level(LoggerManagerThread.Level.INFO, system_info)

        self._log_with_level(LoggerManagerThread.Level.INFO, header)
        self._log_with_level(LoggerManagerThread.Level.INFO, "")

    def start_phase(self, phase):
        """
        Log the start of a new execution phase.

        Args:
            phase (str): The name of the execution phase
        """
        phase_time = time.time()
        self.phase_times[phase] = phase_time

        elapsed = phase_time - self.start_time

        header = self._get_separator(phase)
        self._log_with_level(LoggerManagerThread.Level.INFO, header)

        phase_config = self.EXECUTION_PHASES.get(
            phase, self.EXECUTION_PHASES["HEADER"]
        )
        color = self.COLORS.get(phase_config.get("color", "CYAN"), "")

        timing = f"Starting {color}{phase}{self.COLORS['RESET']} phase (Elapsed: {elapsed:.2f}s)"
        self._log_with_level(LoggerManagerThread.Level.INFO, timing)

        LoggerManager().set_current_phase(phase)

    def end_phase(self, phase):
        """
        Log the end of an execution phase.

        Args:
            phase (str): The name of the execution phase
        """
        if phase in self.phase_times:
            phase_start = self.phase_times[phase]
            phase_duration = time.time() - phase_start

            if phase == "EXECUTION":
                LoggerManager().flush_thread_logs()

            phase_config = self.EXECUTION_PHASES.get(
                phase, self.EXECUTION_PHASES["HEADER"]
            )
            color = self.COLORS.get(phase_config.get("color", "CYAN"), "")

            self._log_with_level(LoggerManagerThread.Level.INFO, "")
            message = f"Completed {color}{phase}{self.COLORS['RESET']} phase (Duration: {phase_duration:.2f}s)"
            self._log_with_level(LoggerManagerThread.Level.INFO, message)

            completed_text = f"{color}{phase} COMPLETED{self.COLORS['RESET']}"

            separator = self._get_separator(phase).replace(
                phase, completed_text
            )
            self._log_with_level(LoggerManagerThread.Level.INFO, separator)
            self._log_with_level(LoggerManagerThread.Level.INFO, "")

            if phase == "EXECUTION":
                LoggerManager().set_current_phase(None)

    def end_execution(self, success=True, exit_code=None):
        """
        Log the end of execution with a summary.

        Args:
            success (bool): Whether execution was successful.
            exit_code (ExitCode): The exit code to include in the log if execution completed with errors.
        """
        total_time = time.time() - self.start_time

        self._log_with_level(LoggerManagerThread.Level.INFO, "")

        phase = "HEADER"
        status = (
            "COMPLETED SUCCESSFULLY"
            if success
            else f"COMPLETED WITH ERRORS ({exit_code})"
        )
        color_prefix = self.COLORS["GREEN"] if success else self.COLORS["RED"]

        header = self._get_separator(phase).replace(
            "HEADER", f"{color_prefix}{status}{self.COLORS['RESET']}"
        )
        self._log_with_level(LoggerManagerThread.Level.INFO, header)

        summary = f"Total execution time: {total_time:.2f}s"
        self._log_with_level(LoggerManagerThread.Level.INFO, summary)

        time.sleep(0.5)

    def log_initialization(self, message, level=LoggerManagerThread.Level.INFO):
        """
        Log a message in the initialization phase with visual formatting.

        Args:
            message (str): The message to log
            level (int): The logging level
        """
        self._log_with_level(level, f"{self.COLOR_PREFIXES['INIT']}{message}")

    def log_setup(self, message, level=LoggerManagerThread.Level.INFO):
        """
        Log a message in the setup phase with visual formatting.

        Args:
            message (str): The message to log
            level (int): The logging level
        """
        self._log_with_level(level, f"{self.COLOR_PREFIXES['SETUP']}{message}")

    def log_execution(self, message, level=LoggerManagerThread.Level.INFO):
        """
        Log a message in the execution phase with visual formatting.
        Args:
            message (str): The message to log
            level (int): The logging level
        """
        self._log_with_level(level, f"{self.COLOR_PREFIXES['EXEC']}{message}")

    def log_post_execution(self, message, level=LoggerManagerThread.Level.INFO):
        """
        Log a message in the post-execution phase with visual formatting.

        Args:
            message (str): The message to log
            level (int): The logging level
        """
        self._log_with_level(level, f"{self.COLOR_PREFIXES['POST']}{message}")

    def log_timeout(self, time_limit, unit="seconds"):
        """
        Log a timeout event with clear visual indication.

        Args:
            time_limit: The time limit that was reached
        """
        timeout_msg = (
            f"TIME LIMIT REACHED: Execution stopped after {time_limit} {unit}"
        )
        color_msg = f"{self.COLORS['YELLOW']}{self.COLORS['BOLD']}{timeout_msg}{self.COLORS['RESET']}"
        self._log_with_level(LoggerManagerThread.Level.WARNING, color_msg)

        separator = "-" * 40
        self._log_with_level(LoggerManagerThread.Level.INFO, separator)

    def log_error(self, message):
        """Log an error message."""
        self._log_with_level(LoggerManagerThread.Level.ERROR, message)

    def log_warning(self, message):
        """Log a warning message."""
        self._log_with_level(LoggerManagerThread.Level.WARNING, message)

    def log_debug(self, message):
        """Log a debug message."""
        self._log_with_level(LoggerManagerThread.Level.DEBUG, message)
