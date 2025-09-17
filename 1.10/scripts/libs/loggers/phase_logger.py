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
This module provides a formatter for console logs, enhancing the LogManager
with structured, color-coded output for better readability during execution.
"""

import time
import platform
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


class PhaseLogger:
    """Formats logs for console output with phases, colors, and timing.

    This class acts as a facade over the LogManager, providing a structured
    way to log the different phases of an execution (e.g., SETUP, EXECUTION).
    It automatically adds color-coding, phase separators, and timing information
    to the logs, delegating the final log-writing action to the LogManager.

    Attributes:
        logger_name (str): The name of the logger instance in LogManager to use.
        version (str): The version of the tool, used in the execution header.
        start_time (float): The timestamp when the execution started.
        phase_times (dict): A dictionary mapping phase names to their start times.
    """

    # ANSI color codes for terminal output
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

    # Configuration for different execution phases
    EXECUTION_PHASES = {
        "HEADER": {"label": "Header", "color": "CYAN", "symbol": "="},
        "INITIALIZATION": {"label": "INIT", "color": "GREEN", "symbol": "-"},
        "SETUP": {"label": "SETUP", "color": "BLUE", "symbol": "-"},
        "EXECUTION": {"label": "EXEC", "color": "MAGENTA", "symbol": "-"},
        "POST_EXECUTION": {"label": "POST", "color": "YELLOW", "symbol": "-"},
        "SYS_INFO": {"label": "SYS", "color": "CYAN", "symbol": "="},
    }

    SEPARATOR_LENGTH = 80

    def __init__(self, logger_name: str = "IMC", version: str = "1.10.0"):
        """Initializes the ConsolePhaseLogger.

        Args:
            logger_name (str): The name of the logger to use via LogManager.
            version (str): The version of the tool to display in the header.
        """
        self.logger_name = logger_name
        self.version = version
        self.start_time = None
        self.phase_times = {}

        self._separator_cache = {}
        self._color_prefixes = self._create_color_prefixes()

    def _create_color_prefixes(self) -> dict:
        """Creates a dictionary of color-coded prefixes for log messages.

        This method iterates through the execution phases and generates the
        fully formatted prefix string for each, like '[SETUP] ' or '[EXEC] '.

        Returns:
            dict: A dictionary mapping phase names to their colored prefixes.
        """
        prefixes = {}
        reset = self.COLORS["RESET"]
        for phase, config in self.EXECUTION_PHASES.items():
            if "color" in config:
                color = self.COLORS.get(config["color"], "")
                # Shortening the phase name for the prefix, e.g., INITIALIZATION -> INIT
                prefix_name = phase[:4]
                prefixes[prefix_name] = f"{color}[{config['label']}]{reset} "

        # Add special cases
        prefixes["ERROR"] = f"{self.COLORS['RED']}[ERROR]{reset} "
        prefixes["TIMEOUT"] = f"{self.COLORS['YELLOW']}[TIMEOUT]{reset} "
        return prefixes

    def _get_separator(self, phase: str, title: str = None) -> str:
        """Generates a formatted separator line for a given phase.

        Results are cached to avoid re-computing separators.

        Args:
            phase (str): The execution phase name (e.g., 'SETUP', 'EXECUTION').
            title (str, optional): The text to display in the separator.
                                   If None, the phase name is used.

        Returns:
            str: A formatted separator string with colors and padding.
        """
        title = title if title is not None else phase
        cache_key = (phase, title)
        if cache_key in self._separator_cache:
            return self._separator_cache[cache_key]

        phase_config = self.EXECUTION_PHASES.get(
            phase, self.EXECUTION_PHASES["HEADER"]
        )
        color = self.COLORS.get(phase_config["color"], "")
        symbol = phase_config["symbol"]

        text = f" {title} "
        padding_length = self.SEPARATOR_LENGTH - len(text)
        left_padding = symbol * (padding_length // 2)
        right_padding = symbol * (padding_length - len(left_padding))

        separator = (
            f"{color}{left_padding}{self.COLORS['BOLD']}{text}"
            f"{self.COLORS['RESET']}{color}{right_padding}{self.COLORS['RESET']}"
        )

        self._separator_cache[cache_key] = separator
        return separator

    def _get_system_info(self) -> str:
        """Constructs a string with system and application information.

        Returns:
            str: A formatted string containing OS, Python, and tool versions.
        """
        return (
            f"System: {platform.system()} {platform.release()} | "
            f"Python: {platform.python_version()} | "
            f"IMC Version: {self.version}"
        )

    def _log_with_level(self, level: int, message: str):
        """Logs a message by delegating to the LogManager.

        Args:
            level (int): The logging level (e.g., LogManagerThread.Level.INFO).
            message (str): The message to log.
        """
        LogManager().log(self.logger_name, level, message)

    def start_execution(self):
        """Logs the execution start, including a system information header."""
        self.start_time = time.time()

        self._log_with_level(LogManagerThread.Level.INFO, "")
        header = self._get_separator("SYS_INFO")
        self._log_with_level(LogManagerThread.Level.INFO, header)

        system_info = self._get_system_info()
        self._log_with_level(LogManagerThread.Level.INFO, system_info)

        self._log_with_level(LogManagerThread.Level.INFO, header)
        self._log_with_level(LogManagerThread.Level.INFO, "")

    def start_phase(self, phase: str):
        """Logs the start of a new execution phase with timing information.

        Args:
            phase (str): The name of the execution phase (e.g., 'SETUP').
        """
        phase_time = time.time()
        self.phase_times[phase] = phase_time

        elapsed = (
            (phase_time - self.start_time) if self.start_time is not None else 0
        )

        header = self._get_separator(phase)
        self._log_with_level(LogManagerThread.Level.INFO, header)

        phase_config = self.EXECUTION_PHASES.get(
            phase, self.EXECUTION_PHASES["HEADER"]
        )
        color = self.COLORS.get(phase_config.get("color", "CYAN"), "")

        timing = f"Starting {color}{phase}{self.COLORS['RESET']} phase (Elapsed: {elapsed:.2f}s)"
        self._log_with_level(LogManagerThread.Level.INFO, timing)

        LogManager().set_current_phase(phase)

    def end_phase(self, phase: str):
        """Logs the end of an execution phase with duration.

        Args:
            phase (str): The name of the execution phase.
        """
        if phase in self.phase_times:
            phase_start = self.phase_times[phase]
            phase_duration = time.time() - phase_start

            if phase == "EXECUTION":
                LogManager().flush_thread_logs()

            phase_config = self.EXECUTION_PHASES.get(
                phase, self.EXECUTION_PHASES["HEADER"]
            )
            color = self.COLORS.get(phase_config.get("color", "CYAN"), "")

            self._log_with_level(LogManagerThread.Level.INFO, "")
            message = f"Completed {color}{phase}{self.COLORS['RESET']} phase (Duration: {phase_duration:.2f}s)"
            self._log_with_level(LogManagerThread.Level.INFO, message)

            completed_text = f"{color}{phase} COMPLETED{self.COLORS['RESET']}"
            separator = self._get_separator(phase, title=completed_text)
            self._log_with_level(LogManagerThread.Level.INFO, separator)
            self._log_with_level(LogManagerThread.Level.INFO, "")

            if phase == "EXECUTION":
                LogManager().set_current_phase(None)

    def end_execution(self, success: bool = True, exit_code=None):
        """Logs the final summary of the execution.

        Args:
            success (bool): Whether the execution was successful.
            exit_code: The exit code if execution failed.
        """
        total_time = (
            (time.time() - self.start_time)
            if self.start_time is not None
            else 0
        )

        self._log_with_level(LogManagerThread.Level.INFO, "")

        if success:
            status = "COMPLETED SUCCESSFULLY"
            color = self.COLORS["GREEN"]
        else:
            status = f"COMPLETED WITH ERRORS ({exit_code})"
            color = self.COLORS["RED"]

        title = f"{color}{status}{self.COLORS['RESET']}"
        header = self._get_separator("HEADER", title=title)
        self._log_with_level(LogManagerThread.Level.INFO, header)

        summary = f"Total execution time: {total_time:.2f}s"
        self._log_with_level(LogManagerThread.Level.INFO, summary)

        time.sleep(0.5)

    def log_initialization(
        self, message: str, level: int = LogManagerThread.Level.INFO
    ):
        """Logs a message during the INITIALIZATION phase.

        Args:
            message (str): The message to log.
            level (int): The logging level.
        """
        self._log_with_level(level, f"{self._color_prefixes['INIT']}{message}")

    def log_setup(self, message: str, level: int = LogManagerThread.Level.INFO):
        """Logs a message during the SETUP phase.

        Args:
            message (str): The message to log.
            level (int): The logging level.
        """
        self._log_with_level(level, f"{self._color_prefixes['SETU']}{message}")

    def log_execution(
        self, message: str, level: int = LogManagerThread.Level.INFO
    ):
        """Logs a message during the EXECUTION phase.

        Args:
            message (str): The message to log.
            level (int): The logging level.
        """
        self._log_with_level(level, f"{self._color_prefixes['EXEC']}{message}")

    def log_post_execution(
        self, message: str, level: int = LogManagerThread.Level.INFO
    ):
        """Logs a message during the POST_EXECUTION phase.

        Args:
            message (str): The message to log.
            level (int): The logging level.
        """
        self._log_with_level(level, f"{self._color_prefixes['POST']}{message}")

    def log_timeout(self, time_limit, unit: str = "seconds"):
        """Logs a timeout event.

        Args:
            time_limit: The time limit that was reached.
            unit (str): The unit of the time limit (e.g., 'seconds').
        """
        timeout_msg = (
            f"TIME LIMIT REACHED: Execution stopped after {time_limit} {unit}"
        )
        color_msg = f"{self.COLORS['YELLOW']}{self.COLORS['BOLD']}{timeout_msg}{self.COLORS['RESET']}"
        self._log_with_level(LogManagerThread.Level.WARNING, color_msg)

        separator = "-" * 40
        self._log_with_level(LogManagerThread.Level.INFO, separator)

    def log_error(self, message: str):
        """Logs an error message with the ERROR prefix.

        Args:
            message (str): The error message to log.
        """
        self._log_with_level(
            LogManagerThread.Level.ERROR,
            f"{self._color_prefixes['ERROR']}{message}",
        )

    def log_warning(self, message: str):
        """Logs a warning message.

        Args:
            message (str): The warning message to log.
        """
        self._log_with_level(LogManagerThread.Level.WARNING, message)

    def log_debug(self, message: str):
        """Logs a debug message.

        Args:
            message (str): The debug message to log.
        """
        self._log_with_level(LogManagerThread.Level.DEBUG, message)
