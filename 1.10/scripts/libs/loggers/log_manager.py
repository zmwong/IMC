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

import logging
import threading
import queue
import os
import sys
import time
import copy
from enum import IntEnum
from datetime import datetime
import re
from typing import Optional
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.utils.singleton_meta import SingletonMeta


class LogManager(metaclass=SingletonMeta):
    """
    A singleton logger manager to control multiple logger instances.
    """

    PHASE_EXECUTION = "EXECUTION"
    PHASE_POST_EXECUTION = "POST_EXECUTION"

    def __init__(self):
        self.manager_thread = LogManagerThread()
        self.manager_thread.start()
        self.preserve_loggers = []

        self.current_phase = None
        self.thread_logs = {}
        self.thread_order = []
        self.thread_logs_flushed = False

        self._edac_logger = None

    @property
    def edac_logger(self):
        """Lazy initialization of EDAC logger to avoid circular imports"""
        if self._edac_logger is None:
            from scripts.libs.loggers.edac_logger import EDACLogger

            self._edac_logger = EDACLogger()
        return self._edac_logger

    def enable_edac_provider(self):
        """Enable EDAC provider for memory error detection."""
        self.edac_logger.enable_edac_provider()

    def set_phase(self, phase: str):
        """Set the current execution phase"""
        self.current_phase = phase

    def set_execution_context(self, test_case_summary: str):
        """Set base log directory using timestamp and provided test case summary.

        The directory pattern is: imc_logs/<timestamp>_<summary>/
        Filenames inside do not include timestamps (debug.log, memory_diagnostics.log, pcm_memory.csv).
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_dir = os.path.join(
            os.getcwd(), "imc_logs", f"{timestamp}_{test_case_summary}"
        )
        os.makedirs(base_dir, exist_ok=True)
        self._execution_log_dir = base_dir

    def get_execution_log_dir(self) -> str:
        return getattr(
            self, "_execution_log_dir", os.path.join(os.getcwd(), "imc_logs")
        )

    def create_logger(
        self,
        name: str,
        log_level: Optional[int] = None,
        log_format: Optional[logging.Formatter] = None,
    ) -> logging.Logger:
        """Register a logger with optional level/format."""
        return self.manager_thread.add_logger(name, log_level, log_format)

    def start_execution(self):
        """Mark the start of execution for memory error tracking"""
        self.current_phase = self.PHASE_EXECUTION
        self.thread_logs_flushed = False
        self.edac_logger.start_execution()

    def log(self, name: str, level: int, msg: str, *args, **kwargs):
        """
        Logs a message to the specified logger.

        Args:
            name (str): The name of the logger
            level (int): The logging level for the message
            msg (str): The log message
            thread_name (str, optional): The name of the thread generating the log
        """
        formatted_msg = msg
        if args:
            try:
                formatted_msg = msg % args
            except (ValueError, TypeError) as e:
                self.manager_thread.log(
                    "SYS",
                    LogManagerThread.Level.WARNING,
                    f"Formatting failed for: {msg}. Error: {e}",
                )
                formatted_msg = msg

        thread_name = kwargs.pop("thread_name", None)

        phase = kwargs.pop("phase", None)

        if (
            self.current_phase == self.PHASE_EXECUTION
            or phase == self.PHASE_EXECUTION
        ) and thread_name:
            if thread_name not in self.thread_logs:
                self.thread_logs[thread_name] = []
                self.thread_order.append(thread_name)
                try:
                    self.edac_logger.quick_memory_check(thread_name)
                except Exception as e:
                    self.manager_thread.log(
                        "SYS",
                        LogManagerThread.Level.WARNING,
                        f"quick_memory_check failed for thread '{thread_name}': {e}",
                    )

            self.thread_logs[thread_name].append(
                (name, level, formatted_msg, kwargs)
            )

            if len(self.thread_logs[thread_name]) % 100 == 0:
                try:
                    self.edac_logger.quick_memory_check(thread_name)
                except (AttributeError, OSError) as e:
                    # Skip memory check if EDAC logger is not available or fails
                    pass

            return
        self.manager_thread.log(name, level, formatted_msg, **kwargs)

    def set_preserve_loggers(self, logger_names):
        """
        Set loggers to preserve during stop_all operations.

        Args:
            logger_names (list): List of logger names to preserve
        """
        self.preserve_loggers = logger_names

    def stop_all(self):
        """
        Stops the logging manager thread.
        """
        if self.preserve_loggers:
            for name in list(self.manager_thread.loggers.keys()):
                if name not in self.preserve_loggers:
                    self.manager_thread.stop_logger(name)
        else:
            self.manager_thread.stop()

    def set_logger_level(self, name: str, verbosity: int):
        """
        Updates the logging level of a specific logger based on verbosity.

        Args:
            name (str): The name of the logger.
            verbosity (int): The verbosity level (0 to 5).
        """
        log_level = logging.get_log_level_from_verbosity(verbosity)
        self.manager_thread.update_logger_level(name, log_level)

    def set_current_phase(self, phase):
        """
        Set the current logging phase.

        Args:
            phase (str): The current execution phase
        """
        if phase == self.PHASE_EXECUTION:
            self.edac_logger.execution_start_time = time.time()
        if (
            phase == self.PHASE_POST_EXECUTION
            and self.current_phase == self.PHASE_POST_EXECUTION
        ):
            return

        if (
            self.current_phase == self.PHASE_EXECUTION
            and phase == self.PHASE_POST_EXECUTION
        ):
            time.sleep(2)  # Wait 2 seconds for kernel messages to be available
            self.check_and_log_memory_errors()
            self.flush_thread_logs()

        self.current_phase = phase

    def get_debug_log_file(self):
        """
        Returns the path to the debug log file if debug logging is enabled.

        Returns:
            str or None: Path to the debug log file or None if debug logging is not enabled
        """
        # Return debug log path stored either on LogManager or fallback to manager thread
        return getattr(
            self,
            "debug_log_file",
            getattr(self.manager_thread, "debug_log_file", None),
        )

    def check_and_log_memory_errors(self, thread_name=None):
        """
        Check for memory errors during execution and log them as warnings.
        Delegates to EDACLogger for implementation.

        Args:
            thread_name (str, optional): The name of the thread to check errors for
        """
        if self.current_phase != self.PHASE_EXECUTION:
            return

        try:
            self.edac_logger.check_and_log_memory_errors(thread_name)

        except (AttributeError, OSError) as e:
            # Skip memory error check if EDAC logger is not available or fails
            pass

    def get_thread_memory_status(self, thread_name):
        """
        Get the memory error status for a specific thread.

        Args:
            thread_name (str): The name/PID of the thread

        Returns:
            dict: Dictionary with CE count, UE count, status, and exit_code
        """
        return self.edac_logger.get_thread_memory_status(thread_name)

    def get_thread_exit_code(self, thread_name):
        """
        Get the appropriate exit code for a thread based on memory errors detected.

        Args:
            thread_name (str): The name/PID of the thread

        Returns:
            int: Exit code
        """
        return self.edac_logger.get_thread_exit_code(thread_name)

    def has_thread_memory_errors(self, thread_name):
        """
        Check if a specific thread has memory errors.

        Args:
            thread_name (str): The name of the thread to check

        Returns:
            bool: True if the thread has memory errors
        """
        return self.edac_logger.has_thread_memory_errors(thread_name)

    def has_memory_errors(self):
        """
        Check if any memory errors were detected during execution.

        Returns:
            bool: True if any memory errors were found
        """
        return self.edac_logger.has_memory_errors()

    def flush_thread_logs(self):
        """
        Flush all buffered thread logs in an organized manner.
        """
        if not self.thread_logs or self.thread_logs_flushed:
            return

        self.thread_logs_flushed = True

        self.manager_thread.log("SYS", LogManagerThread.Level.INFO, "")
        self.manager_thread.log(
            "SYS",
            LogManagerThread.Level.INFO,
            "===== THREAD EXECUTION LOGS =====",
        )
        self.manager_thread.log("SYS", LogManagerThread.Level.INFO, "")

        for thread_name in self.thread_order:
            if thread_name not in self.thread_logs:
                continue

            thread_separator = f"----- {thread_name} -----"
            self.manager_thread.log(
                "SYS", LogManagerThread.Level.INFO, thread_separator
            )

            for name, level, msg, kwargs in self.thread_logs[thread_name]:
                self.manager_thread.log(name, level, msg, **kwargs)

            self.manager_thread.log("SYS", LogManagerThread.Level.INFO, "")

        # Post-execution memory analysis
        try:
            self.edac_logger.immediate_post_execution_check()
        except Exception as analysis_error:
            self.manager_thread.log(
                "SYS",
                LogManagerThread.Level.WARNING,
                f"Post-execution memory analysis failed: {analysis_error}",
            )
            try:
                self.edac_logger.check_and_log_memory_errors()
            except Exception:
                self.manager_thread.log(
                    "SYS",
                    LogManagerThread.Level.ERROR,
                    "All memory error checking failed",
                )

        self.thread_logs = {}
        self.thread_order = []

    def handle_emergency_memory_analysis(self):
        """
        This method serves as a emergency coordinator, it forces the system
        into post execution phase to ensure all buffered thread logs are
        processed and memory error detection is performed.

        Behaviour:
            - Forces transition to post_execution phase
            - Flushes all buffered thread logs for immediate visibility
            - Triggers memory error detection and reporting
            - Ensures diagnostic data is preserved for analysis

        Args:
            None: This method takes no parameters

        Returns:
            None: This method performs emergency operations and does not return
                any value. All results are captured in log files and internal
                state tracking.

        """
        self.set_current_phase(self.PHASE_POST_EXECUTION)
        self.flush_thread_logs()


class LogManagerThread(threading.Thread):
    """
    A logging manager that runs in a separate thread

    This class manages logging as multithread
    It uses a queue to process log messages, ensuring that logging
    does not block the main application

    Attributes:
        name (str): The name of the logger.
        log_level (Level): The logging level
        log_format (logging.Formatter): The format for log messages
        queue (queue.Queue): A queue for storing log messages
        _logger (logging.Logger): The logger instance

    This class manages logging as multithread
    It uses a queue to process log messages, ensuring that logging
    does not block the main application

    Attributes:
        name (str): The name of the logger.
        log_level (Level): The logging level
        log_format (logging.Formatter): The format for log messages
        queue (queue.Queue): A queue for storing log messages
        _logger (logging.Logger): The logger instance
    """

    class Level(IntEnum):
        """
        Available logging levels.

        Attributes:
            OFF (int): No messages printed.
            CRITICAL (int): Critical messages only.
            ERROR (int): Error messages and above.
            WARNING (int): Warning messages and above.
            INFO (int): Informational messages and above.
            DEBUG (int): Debug messages and above.
        """

        OFF = 60  # No messages printed
        CRITICAL = logging.CRITICAL  # 50 - Least messages printed
        ERROR = logging.ERROR  # 40
        WARNING = logging.WARNING  # 30
        INFO = logging.INFO  # 20
        DEBUG = logging.DEBUG  # 10 - All messages above

    def __init__(self):
        super().__init__()
        self.loggers = {}
        self.lock = threading.Lock()
        self._running = True
        self.daemon = True
        """
            Initializes the LogManagerThread.

            Args:
                name (str, optional): The name of the logger
                log_level (Level, optional): The logging level
                log_format (logging.Formatter, optional): The format for log messages
            """

    def add_logger(
        self,
        name: str,
        log_level: Optional[IntEnum] = None,
        log_format: Optional[logging.Formatter] = None,
    ):
        """
        Adds a logger to the manager.

        Args:
            name (str): The name of the logger.
            log_level (Level, optional): The logging level. Defaults to `Level.WARNING`.
            log_format (logging.Formatter, optional): The format for log messages.
                Defaults to a standard format with timestamps.
        """
        with self.lock:
            if name not in self.loggers:
                queue_ = queue.Queue()
                logger = self._setup_logger(name, log_level, log_format)
                self.loggers[name] = {
                    "queue": queue_,
                    "logger": logger,
                }

    def _setup_logger(
        self,
        name: str,
        log_level: Optional[int],
        log_format: Optional[logging.Formatter],
    ) -> logging.Logger:
        """
        Sets up the logger with handlers for stdout and stderr.

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger = logging.getLogger(name)
        actual_level = (
            log_level if log_level is not None else self.Level.WARNING
        )

        logger.setLevel(self.Level.DEBUG)
        for handler in logger.handlers:
            logger.removeHandler(handler)

        formatter = log_format or logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )

        if actual_level != self.Level.OFF:

            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(formatter)
            stdout_handler.setLevel(actual_level)

            class LevelFilter(logging.Filter):
                def __init__(self, min_level, max_level=None):
                    self.min_level = min_level
                    self.max_level = (
                        max_level
                        if max_level is not None
                        else logging.CRITICAL + 1
                    )

                def filter(self, record):
                    return self.min_level <= record.levelno < self.max_level

            stdout_handler.addFilter(
                LevelFilter(actual_level, self.Level.CRITICAL)
            )
            logger.addHandler(stdout_handler)

            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setFormatter(formatter)
            stderr_handler.setLevel(self.Level.CRITICAL)
            logger.addHandler(stderr_handler)

            if not hasattr(self, "_shared_file_handler"):
                from scripts.libs.loggers.log_manager import LogManager as _LM

                log_dir = _LM().get_execution_log_dir()
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, "debug.log")
                # store on thread and singleton for external access
                self.debug_log_file = log_file
                _LM().debug_log_file = log_file
                self._shared_file_handler = logging.FileHandler(log_file)
                self._shared_file_handler.setLevel(self.Level.DEBUG)

                class NoColorFormatter(logging.Formatter):
                    """Formatter that strips ANSI color codes from log messages"""

                    ansi_escape = re.compile(
                        r"\x1B(?:[@-Z\\-_]|\[[0-9;]*[ -/]*[@-~])"
                    )

                    def format(self, record):
                        if isinstance(record.msg, str):
                            record = copy.copy(record)
                            record.msg = self.ansi_escape.sub("", record.msg)
                        return super().format(record)

                file_formatter = NoColorFormatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "%Y-%m-%d %H:%M:%S",
                )
                self._shared_file_handler.setFormatter(file_formatter)

            logger.addHandler(self._shared_file_handler)

        return logger

    def log(self, name: str, level: int, msg: str, *args, **kwargs):
        """
        Adds a log message to the queue.

        Args:
            level (int): The logging level for the message.
            msg (str): The log message.
            *args: Additional arguments for the log message.
            **kwargs: Additional keyword arguments for the log message.
        """
        with self.lock:
            if name in self.loggers:
                record = self.loggers[name]["logger"].makeRecord(
                    name,
                    level,
                    fn="",
                    lno=0,
                    msg=msg,
                    args=args,
                    exc_info=None,
                    func=None,
                    extra=None,
                )
                self.loggers[name]["queue"].put(record)

    def run(self):
        while self._running:
            self._process_log_queue()
            time.sleep(0.01)

        self._process_log_queue(flush_all=True)

    def _process_log_queue(self, flush_all=False):
        """
        Process pending log messages in the queue.

        Args:
            flush_all (bool): If True, will try to flush all logs even from empty queues
        """
        with self.lock:
            for logger_data in self.loggers.values():
                while True:
                    try:
                        record = logger_data["queue"].get_nowait()
                        logger_data["logger"].handle(record)
                    except queue.Empty:
                        break

                if flush_all and logger_data["logger"].handlers:
                    for handler in logger_data["logger"].handlers:
                        if hasattr(handler, "flush"):
                            handler.flush()

    class StdoutFilter(logging.Filter):
        """
        A simple logging filter for stdout.

        This filter ensures that only messages with levels DEBUG, INFO, WARNING,
        or ERROR are sent to stdout.
        """

        def filter(self, record: logging.LogRecord) -> bool:
            """
            Filters log records for stdout.

            Args:
                record (logging.LogRecord): The log record to filter.

            Returns:
                bool: `True` if the record should be logged to stdout, `False` otherwise.
            """
            return record.levelno in (
                LogManagerThread.Level.DEBUG,
                LogManagerThread.Level.INFO,
                LogManagerThread.Level.WARNING,
                LogManagerThread.Level.ERROR,
            )

    def stop_logger(self, name: str):
        """
        Stops the logger thread for the specified logger.

        Args:
            name (str): The name of the logger to stop.
        """
        with self.lock:
            if name in self.loggers:
                del self.loggers[name]

    def resume_logger(
        self,
        name: str,
        log_level: Optional[int] = None,
        log_format: Optional[logging.Formatter] = None,
    ):
        """
        Resumes the logger thread for the specified logger.

        Args:
            name (str): The name of the logger to resume
            log_level (Level, optional): The logging level
            log_format (logging.Formatter, optional): The format for log messages
        """
        with self.lock:
            if name not in self.loggers:
                self.add_logger(name, log_level, log_format)

    def update_logger_level(self, name: str, log_level: int):
        """
        Updates the logging level of a specific logger.

        Args:
            name (str): The name of the logger.
            log_level (int): The new logging level.
        """
        with self.lock:
            if name in self.loggers:
                logger = self.loggers[name]["logger"]
                if logger.handlers and all(
                    handler.level == log_level for handler in logger.handlers
                ):
                    return

                for handler in logger.handlers:
                    if handler.level != log_level:
                        handler.setLevel(log_level)

                        for filter_obj in handler.filters:
                            if hasattr(filter_obj, "min_level"):
                                filter_obj.min_level = log_level

    def has_logger(self, name: str) -> bool:
        """
        Checks if a logger with the given name exists.

        Args:
            name (str): The name of the logger to check

        Returns:
            bool: True if logger exists, False otherwise
        """
        with self.lock:
            return name in self.loggers

    def stop(self):
        """
        Stops the logging thread.

        This method sends a signal for the thread
        to stop processing log messages and ensures all pending logs are flushed.
        """
        self._running = False
        self._process_log_queue(flush_all=True)

        time.sleep(0.1)

    @classmethod
    def pretty_exit(cls, logger_name: str, exit_code: ExitCode):
        """
        Logs an appropriate message and exits the program with the given exit code.

        Args:
            logger_name (str): Name of the logger to use for the exit message.
            exit_code (ExitCode): The exit code to log and use for exiting the program.

        Example:
            ```
            LogManagerThread.pretty_exit("MyLogger", ExitCode.OK)
            ```
        """
        exit_str = f"EXIT_CODE: {exit_code} ({int(exit_code)})"
        log_manager = LogManager()

        if exit_code == ExitCode.OK:
            log_manager.log(logger_name, cls.Level.INFO, exit_str)
        elif exit_code in (
            ExitCode.RUNNER_TOOL_FAILED,
            ExitCode.TOOL_CONFIGURATION_ERROR,
        ):
            log_manager.log(logger_name, cls.Level.CRITICAL, exit_str)
        else:
            log_manager.log(logger_name, cls.Level.WARNING, exit_str)

        log_manager.stop_all()
        sys.exit(int(exit_code))
