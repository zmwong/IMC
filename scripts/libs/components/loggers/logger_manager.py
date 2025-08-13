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


class LoggerManager(metaclass=SingletonMeta):
    """
    A singleton logger manager to control multiple logger instances.
    """

    PHASE_EXECUTION = "EXECUTION"

    def __init__(self):
        self.manager_thread = LoggerManagerThread()
        self.manager_thread.start()
        self.preserve_loggers = []

        self.current_phase = None
        self.thread_logs = {}
        self.thread_order = []

    def create_logger(
        self,
        name: str,
        log_level: Optional[IntEnum] = None,
        log_format: Optional[logging.Formatter] = None,
    ):
        """
        Creates and registers a new LoggerManagerThread
        Attributes:
        name (str): Name of the logger
        log_level (level): Available logging level
        log_format: Logger specific style

        """
        self.manager_thread.add_logger(name, log_level, log_format)

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
            except Exception:
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
            self.thread_logs[thread_name].append(
                (name, level, formatted_msg, kwargs)
            )
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
        if (
            self.current_phase == self.PHASE_EXECUTION
            and phase != self.PHASE_EXECUTION
        ):
            self.flush_thread_logs()

        self.current_phase = phase

    def get_debug_log_file(self):
        """
        Returns the path to the debug log file if debug logging is enabled.

        Returns:
            str or None: Path to the debug log file or None if debug logging is not enabled
        """
        return getattr(self.manager_thread, "debug_log_file", None)

    def flush_thread_logs(self):
        """
        Flush all buffered thread logs in an organized manner.
        """
        if not self.thread_logs:
            return

        self.manager_thread.log("SYS", LoggerManagerThread.Level.INFO, "")
        self.manager_thread.log(
            "SYS",
            LoggerManagerThread.Level.INFO,
            "===== THREAD EXECUTION LOGS =====",
        )
        self.manager_thread.log("SYS", LoggerManagerThread.Level.INFO, "")

        for thread_name in self.thread_order:
            if thread_name not in self.thread_logs:
                continue

            thread_separator = f"----- {thread_name} -----"
            self.manager_thread.log(
                "SYS", LoggerManagerThread.Level.INFO, thread_separator
            )

            for name, level, msg, kwargs in self.thread_logs[thread_name]:
                self.manager_thread.log(name, level, msg, **kwargs)

            self.manager_thread.log("SYS", LoggerManagerThread.Level.INFO, "")

        self.thread_logs = {}
        self.thread_order = []


class LoggerManagerThread(threading.Thread):
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
            Initializes the LoggerManagerThread.

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

            if actual_level == self.Level.DEBUG:
                log_dir = os.path.join(os.getcwd(), "imc_logs")
                os.makedirs(log_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                log_file = os.path.join(log_dir, f"imc_debug_{timestamp}.log")
                self.debug_log_file = log_file

                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(self.Level.DEBUG)

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
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)

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
                LoggerManagerThread.Level.DEBUG,
                LoggerManagerThread.Level.INFO,
                LoggerManagerThread.Level.WARNING,
                LoggerManagerThread.Level.ERROR,
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
            LoggerManagerThread.pretty_exit("MyLogger", ExitCode.OK)
            ```
        """
        exit_str = f"EXIT_CODE: {exit_code} ({int(exit_code)})"
        log_manager = LoggerManager()

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
