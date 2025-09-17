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
This module provides the base definition for the threads used by a runnable.
The `BaseThread` class defines a base implementation for threads that handle
subprocess execution. It provides methods for creating subprocesses, reading
data from pipes, and managing thread-specific subprocess objects.
"""
import threading
import queue
import subprocess
import collections
from scripts.libs.components.os_system.abstract_system import AbstractSystem
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


class BaseThread(threading.Thread):
    """
    Base class for threads used by a runnable.
    The `BaseThread` class provides a base implementation for threads that
    execute subprocesses. Each thread manages a specific subprocess object
    and provides utility methods for reading data from pipes and handling
    subprocess execution.
    Attributes:
        proc (subprocess.Popen): The subprocess object managed by the thread.
    """

    def __init__(self):
        """
        Initializes the BaseThread class.
        This constructor initializes the `proc` attribute to `None`, which
        will later hold the subprocess object managed by the thread.
        Example:
            ```
            thread = BaseThread()
            thread.start()
            ```
        """
        super().__init__()
        self.proc = None
        # Tracks whether the subprocess managed by this thread is currently halted/suspended.
        # This flag is maintained by OS-specific halt/resume operations for reliable state checks.
        self.halted = False

    @classmethod
    def _pipe_reader(cls, pipe, logger_name, log_level) -> str:
        """
        Reads data from a subprocess pipe and logs each line.
        This method reads data line by line from the provided pipe. It ignores
        lines containing specific substrings (e.g., "[debug]", "[info]") and
        logs each line as it is read. The remaining data is returned as a single string.
        Args:
            pipe (subprocess.PIPE): The pipe to read data from.
            logger_name (str): The name of the logger to use for logging.
            log_level (LogManagerThread.Level): The log level to use for logging.
        Returns:
            str: The data read from the pipe.
        Example:
            ```
            stdout_data = BaseThread._pipe_reader(proc.stdout, "LoggerName", LogManagerThread.Level.INFO)
            print(stdout_data)
            ```
        """
        ignore_lines = ["debug", "info"]
        read_data = ""
        try:
            with pipe:
                thread_name = threading.current_thread().name
                logger_manager = LogManager()
                for line in iter(pipe.readline, ""):
                    if any(bad_str in line for bad_str in ignore_lines):
                        continue
                    read_data += line
                    logger_manager.log(
                        "SYS",
                        log_level,
                        line.rstrip(),
                        thread_name=thread_name,
                        phase="EXECUTION",
                    )
        except ValueError:
            # Pipe is closed
            pass
        return read_data

    def create_subprocess(
        self,
        exec_list: list,
        data_queue: queue.Queue,
        pid_queue: queue.Queue,
        os_system: AbstractSystem,
    ):
        """
        Executes a subprocess and retrieves its information.
        This method creates a subprocess using the provided execution list and
        manages its lifecycle. It reads the subprocess's stdout and stderr, waits
        for its completion, and stores the results in the provided data queue.
        Args:
            exec_list (list): The command and arguments to execute as a subprocess.
            data_queue (queue.Queue): A queue to store the subprocess results.
            pid_queue (queue.Queue): A queue to store the subprocess PID.
            os_system (AbstractSystem): The operating system abstraction for managing
                subprocess creation flags.
        Returns:
            None
        Raises:
            Exception: If an error occurs during subprocess creation or execution.
        Example:
            ```
            thread = BaseThread()
            thread.create_subprocess(
                exec_list=["python", "script.py"],
                data_queue=data_queue,
                pid_queue=pid_queue,
                os_system=os_system,
            )
            ```
        """
        creation_flags = os_system.creation_flags
        test_result = collections.namedtuple(
            "TestResult", "pid stdout stderr exitcode"
        )
        try:
            self.proc = subprocess.Popen(
                exec_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                encoding="utf-8",
                creationflags=creation_flags,
            )
            LogManager().log(
                "SYS",
                LogManagerThread.Level.DEBUG,
                f"PID-{self.proc.pid} about to start using {' '.join(exec_list)}",
                thread_name=self.name,
                phase="EXECUTION",
            )
            pid_queue.put(self.proc.pid)  # Notify the parent process of the PID

            lpu = getattr(self, "lpu", None)
            if lpu is None:
                lpu = LogManager().edac_logger._extract_lpu_from_command(
                    exec_list
                )
            LogManager().edac_logger.register_thread(
                self.name, self.proc.pid, lpu
            )

            stdout = self._pipe_reader(
                self.proc.stdout, "SYS", LogManagerThread.Level.INFO
            )
            stderr = self._pipe_reader(
                self.proc.stderr, "SYS", LogManagerThread.Level.ERROR
            )
            self.proc.wait()
            data_queue.put(
                test_result(
                    pid=self.proc.pid,
                    stdout=stdout,
                    stderr=stderr,
                    exitcode=self.proc.returncode,
                )
            )
        except Exception as e:
            LogManager().log(
                "SYS",
                LogManagerThread.Level.ERROR,
                f"An error occurred when launching the subprocess: {e}",
                thread_name=self.name,
                phase="EXECUTION",
            )
        finally:
            if self.proc:
                if self.proc.stdout:
                    self.proc.stdout.close()
                if self.proc.stderr:
                    self.proc.stderr.close()
                self.proc.terminate()
                self.proc.wait()
