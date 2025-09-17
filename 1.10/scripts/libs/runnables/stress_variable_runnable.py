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
"""Stress variable runnable with sine wave modulation for dynamic memory testing.

This module implements a variable stress testing pattern that uses sine wave modulation
to dynamically adjust the number of active threads during memory validation testing.
Instead of constant full-capacity execution, this approach creates varying stress
patterns that can help reveal memory issues under different load conditions.

The stress modulation is achieved by:
    - Using a normalized sine wave function to calculate target stress levels (0-1 range)
    - Dynamically halting/resuming threads based on the calculated stress level
    - Running a background control thread that adjusts thread states at regular intervals

Additional features:
    - PCM (Performance Counter Monitor) integration for performance data collection
    - Configurable stress periods and control intervals
    - Comprehensive logging and error handling

This approach is particularly useful for:
    - Detecting memory issues that only appear under specific load conditions
    - Testing system behavior under varying stress patterns
    - Simulating real-world workload patterns in memory validation scenarios
    - Collecting performance metrics during variable stress testing

Example:
    Basic usage with default 60-second sine wave period:
        
        distribution = SomeDistribution()
        executor = SomeExecutor()
        tool_manager = SomeToolManager()
        
        runnable = StressVariableRunnable(distribution, executor, tool_manager)
        exit_code = runnable.execute()
        
    With PCM monitoring enabled:
        # Enable PCM via command line: --pcm --pcm_path /path/to/pcm-memory

Attributes:
    STRESS_PERIOD_DEFAULT (float): Default sine wave period in seconds (60.0).
    CONTROL_INTERVAL (float): Background thread control interval in seconds (0.25).
"""
import argparse
import math
import threading
import time
from typing import List, Optional
from scripts.libs.loggers import level_to_verbosity
from scripts.libs.runnables.abstract_runnable import AbstractRunnable
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)
from scripts.libs.loggers.phase_logger import PhaseLogger
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.system_handler import SystemHandler
from scripts.libs.plugins.pcm.pcm_memory_plugin import PCMMemoryPlugin


# Module-level constants
STRESS_PERIOD_DEFAULT = 60.0  # Default sine wave period in seconds
CONTROL_INTERVAL = 0.25  # Background thread control interval in seconds


class StressVariableRunnable(AbstractRunnable):
    """A stress variable implementation that modulates stress using sine wave patterns.

    The StressVariableRunnable class extends the default runnable behavior by adding
    a background thread that periodically adjusts the number of active threads based
    on a sine wave function. This creates variable stress patterns instead of constant
    full-capacity execution.

    The stress level is calculated using a normalized sine wave (0-1 range), and the
    number of active threads is adjusted accordingly using halt/resume signals.

    The sine wave modulation follows the formula:
        stress_level = (sin(2π * elapsed_time / period) + 1) / 2

    This ensures the stress level varies smoothly between 0 (no threads active) and
    1 (all threads active) over the specified period.

    Attributes:
        tool_manager: An object responsible for managing tool-specific data and operations.
            Must provide logger_name, tool_data.parsed_args, and TOOL_NAME attributes.
        distribution: The distribution strategy for generating execution commands.
            Must implement generate_commands() method.
        executor: The executor that manages thread instances. Must provide live_threads()
            and executeInstances() methods.
        logger (PhaseLogger): Logger instance for execution phase tracking.
        stress_period (float): The period of the sine wave in seconds. Defaults to 60.0
            if not specified in parsed_args.stress_period.
        control_interval (float): The control interval for stress adjustments in seconds.
            Defaults to 0.25 if not specified in parsed_args.stress_control_interval.
        stress_control_thread (threading.Thread): Background thread controlling stress levels.
            Runs the _stress_control_worker method.
        stop_stress_control (threading.Event): Event to signal the stress control thread to stop.

    Note:
        The stress control thread runs as a daemon thread and will be automatically
        terminated when the main program exits.
    """

    def __init__(self, distribution, executor, tool_manager) -> None:
        """Initialize the StressVariableRunnable with required components.

        Sets up the variable stress runnable with the provided distribution, executor,
        and tool manager. Initializes logging, extracts stress period and control interval
        configuration, and prepares the stress control mechanisms.

        Args:
            distribution: The distribution strategy for generating execution commands.
                Must implement generate_commands() method.
            executor: The executor that manages thread instances. Must provide
                live_threads() and executeInstances() methods.
            tool_manager: Tool manager instance containing configuration and logger setup.
                Must have logger_name, tool_data.parsed_args attributes.

        Note:
            The stress_period is extracted from tool_manager.tool_data.parsed_args.stress_period
            if available, otherwise defaults to 60.0 seconds.
            The control_interval is extracted from tool_manager.tool_data.parsed_args.stress_control_interval
            if available, otherwise defaults to 0.25 seconds.
        """
        super().__init__(distribution, executor, tool_manager)

        # Initialize the logger
        LogManager().create_logger(
            name=self.tool_manager.logger_name,
            log_level=level_to_verbosity(
                self.tool_manager.tool_data.parsed_args.verbosity
            ),
        )

        self.logger = PhaseLogger(logger_name=self.tool_manager.logger_name)

        # Stress modulation parameters
        try:
            self.stress_period = (
                self.tool_manager.tool_data.parsed_args.stress_period
            )
        except AttributeError:
            self.stress_period = STRESS_PERIOD_DEFAULT  # Default period

        try:
            self.control_interval = (
                self.tool_manager.tool_data.parsed_args.stress_control_interval
            )
        except AttributeError:
            self.control_interval = CONTROL_INTERVAL  # Default control interval
        self.stress_control_thread: Optional[threading.Thread] = None
        self.stop_stress_control: threading.Event = threading.Event()

    def parse_args_list(self, argv: List[str]) -> argparse.Namespace:
        """Parse command-line arguments by delegating to the tool manager.

        This method serves as a wrapper around the tool manager's argument parsing
        functionality to maintain consistency with the AbstractRunnable interface.

        Args:
            argv: List of command-line argument strings to parse.

        Returns:
            argparse.Namespace: Parsed arguments namespace containing all configuration
                options including stress_period if specified.

        Raises:
            Any exceptions raised by the underlying tool_manager.parse_args_list() method.
        """
        return self.tool_manager.parse_args_list(argv)

    def _calculate_stress_level(self, elapsed_time: float) -> float:
        """Calculate the current stress level using a normalized sine wave.

        Uses a sine wave function to create a smooth stress variation over time.
        The sine wave is normalized to ensure stress levels range from 0.0 to 1.0.

        The calculation follows: stress_level = (sin(2π * elapsed_time / period) + 1) / 2

        This produces:
        - 0.0 at the sine wave minimum (0% stress, all threads halted)
        - 1.0 at the sine wave maximum (100% stress, all threads active)
        - Smooth transitions between these extremes

        Args:
            elapsed_time: Time elapsed since execution start in seconds. Must be >= 0.

        Returns:
            float: Normalized stress level between 0.0 and 1.0 inclusive.

        Note:
            The stress pattern repeats every self.stress_period seconds.
        """
        # Normalize sine wave to range [0, 1]
        # sin(x) ranges [-1, 1], so (sin(x) + 1) / 2 gives [0, 1]
        angle = 2 * math.pi * elapsed_time / self.stress_period
        return (math.sin(angle) + 1) / 2

    def _calculate_active_threads(
        self, stress_level: float, total_threads: int
    ) -> int:
        """Calculate how many threads should be active based on stress level.

        Determines the optimal number of active threads to achieve the target
        stress level. Uses ceiling function to ensure we don't under-achieve
        the target stress level when thread counts don't divide evenly.

        The calculation assumes each thread contributes equally to the total stress:
        - Each thread contributes: 1/total_threads to total stress
        - Required threads = stress_level / (1/total_threads)
        - Result is ceiling of required threads to ensure target is met or exceeded

        Args:
            stress_level: Target stress level between 0.0 and 1.0 inclusive.
                0.0 means no threads should be active, 1.0 means all threads active.
            total_threads: Total number of available threads. Must be >= 0.

        Returns:
            int: Number of threads that should be active, between 0 and total_threads
                inclusive. Returns 0 if total_threads is 0.

        Note:
            The result is rounded to 10 decimal places to avoid floating-point
            precision issues before applying ceiling function.
        """
        if total_threads == 0:
            return 0

        # Each thread contributes 1/total_threads to the total stress
        thread_contribution = 1.0 / total_threads

        # Calculate required threads and ceil to ensure we don't go under target
        required_threads = stress_level / thread_contribution
        # Round to avoid floating point precision issues
        required_threads = round(required_threads, 10)
        return min(total_threads, max(0, math.ceil(required_threads)))

    def _stress_control_worker(self) -> None:
        """Background worker thread that modulates stress by halting/resuming threads.

        This method runs in a separate daemon thread and continuously adjusts thread
        states to match the target stress level calculated from the sine wave function.

        The control loop performs these steps at the configured control interval:
        1. Calculates the current target stress level using elapsed time and sine wave
        2. Determines how many threads should be active for that stress level
        3. Counts currently active (non-halted) threads
        4. Adjusts thread states by halting excess threads or resuming halted threads
        5. Logs debug information about stress levels and thread states

        Thread state management:
        - To increase active threads: Resume halted threads first
        - To decrease active threads: Halt currently active threads
        - Uses SystemHandler().os_system.halt_thread() and resume_thread() methods
        - Checks thread.halted attribute to determine current state

        The control interval (self.control_interval) balances responsiveness with overhead,
        providing smooth stress transitions without excessive system calls. Default is
        0.25 seconds but can be configured via --stress-control-interval parameter.

        Raises:
            Logs warnings for any exceptions during stress control but continues operation.
            The thread stops when self.stop_stress_control event is set.

        Note:
            This method is designed to run as a daemon thread and will exit gracefully
            when the main execution completes.
        """
        start_time = time.time()
        control_interval = (
            self.control_interval
        )  # Use configurable control interval

        LogManager().log(
            self.tool_manager.logger_name,
            LogManagerThread.Level.INFO,
            f"Starting stress control with period {self.stress_period}s, control interval {self.control_interval}s",
        )

        while not self.stop_stress_control.wait(control_interval):
            try:
                elapsed_time = time.time() - start_time
                current_stress = self._calculate_stress_level(elapsed_time)

                live_threads = self.executor.live_threads()
                total_threads = len(live_threads)

                if total_threads == 0:
                    continue

                target_active = self._calculate_active_threads(
                    current_stress, total_threads
                )

                # Count currently active (not halted) threads using explicit halted state
                currently_active = sum(
                    1
                    for thread in live_threads
                    if not getattr(thread, "halted", False)
                )

                # Adjust thread states
                if currently_active < target_active:
                    # Need to resume some threads: pick halted ones first
                    need = target_active - currently_active
                    for thread in live_threads:
                        if need <= 0:
                            break
                        if getattr(thread, "halted", False):
                            SystemHandler().os_system.resume_thread(thread)
                            if not getattr(thread, "halted", False):
                                need -= 1

                elif currently_active > target_active:
                    # Need to halt some threads
                    to_halt = currently_active - target_active
                    for thread in live_threads:
                        if to_halt <= 0:
                            break
                        if not getattr(thread, "halted", False):
                            # Try to halt the thread
                            SystemHandler().os_system.halt_thread(thread)
                            if getattr(thread, "halted", False):
                                to_halt -= 1

            except Exception as e:
                LogManager().log(
                    self.tool_manager.logger_name,
                    LogManagerThread.Level.WARNING,
                    f"Error in stress control: {str(e)}",
                )

        LogManager().log(
            self.tool_manager.logger_name,
            LogManagerThread.Level.INFO,
            "Stress control thread stopped",
        )

    def _execute(self):
        """Execute the tool with variable stress using sine wave modulation and PCM monitoring.

        This method extends the default execution pattern by adding dynamic stress
        control through a background thread and optional PCM (Performance Counter Monitor)
        integration. The execution flow includes:

        1. **Initialization Phase**:
           - Initialize PCM monitoring if enabled via --pcm flag
           - Generate execution commands using the distribution strategy
           - Set up execution state tracking (time_limit_reached, execution_completed)
           - Configure logging with execution parameters and stress period

        2. **Execution Phase**:
           - Start the background stress control thread
           - Execute all tool instances using the executor
           - Monitor execution progress and handle time-based limits
           - PCM runs in parallel collecting performance data

        3. **Stress Control**:
           - Background thread modulates active thread count using sine wave
           - Provides variable stress patterns instead of constant load
           - Automatically stops when execution completes

        4. **Post-Processing Phase**:
           - Stop the stress control thread gracefully
           - Run tool manager post-processing
           - Generate final execution logs and determine exit code

        5. **Cleanup Phase**:
           - Stop and join PCM monitoring thread
           - Ensure all resources are properly released

        Returns:
            ExitCode: The result of tool execution. ExitCode.OK indicates successful
                execution without errors. Other values indicate various failure modes.

        Raises:
            Exception: Re-raises any post-processing errors after logging them.
                Execution errors are caught, logged, and stored in tool_data but
                don't immediately raise exceptions.

        Note:
            Both the stress control thread and PCM monitoring thread are managed as
            daemons and will be automatically cleaned up. A 5-second timeout is used
            when joining threads to prevent hanging on shutdown.
        """
        self.tool_manager.tool_data.data["time_limit_reached"] = False
        self.tool_manager.tool_data.data["execution_completed"] = False
        logger = self.tool_manager.logger
        pcm = None

        # Initialize PCM monitoring if enabled
        if (
            hasattr(self.tool_manager.tool_data.parsed_args, "pcm")
            and self.tool_manager.tool_data.parsed_args.pcm
        ):
            # Initialize PCM monitoring - don't join immediately so it runs in background
            pcm = PCMMemoryPlugin(
                self.tool_manager.tool_data.parsed_args.pcm_path,
                delay=self.tool_manager.tool_data.parsed_args.pcm_delay,
            )
            pcm.start()
            LogManager().log(
                self.tool_manager.logger_name,
                LogManagerThread.Level.INFO,
                "PCM monitoring started for variable stress execution",
            )

        try:
            commands = self.distribution.generate_commands()
            command_count = len(commands) if commands else 0

            init_message = f"Generated {command_count} execution commands (Variable Stress Mode)"

            parsed_args = self.tool_manager.tool_data.parsed_args
            if (
                hasattr(parsed_args, "time_to_execute")
                and parsed_args.time_to_execute
            ):
                time_limit = parsed_args.time_to_execute
                init_message += (
                    f" | Time-based execution: {time_limit} second(s)"
                )

            init_message += f" | Stress period: {self.stress_period}s | Control interval: {self.control_interval}s"

            logger.log_initialization(init_message)

            logger.start_phase("EXECUTION")
            logger.log_execution(
                f"Executing {self.tool_manager.TOOL_NAME} instances with variable stress..."
            )

            LogManager().set_preserve_loggers(
                [self.tool_manager.logger_name, "SYS"]
            )

            # Start the stress control thread before executing instances
            self.stress_control_thread = threading.Thread(
                target=self._stress_control_worker, name="StressControl"
            )
            self.stress_control_thread.daemon = True
            self.stress_control_thread.start()

            # Execute instances (this will start all threads)
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
        finally:
            # Stop the stress control thread
            self.stop_stress_control.set()
            if (
                self.stress_control_thread
                and self.stress_control_thread.is_alive()
            ):
                self.stress_control_thread.join(timeout=5.0)

            # Stop PCM monitoring if it was started
            if pcm:
                pcm.stop()
                LogManager().log(
                    self.tool_manager.logger_name,
                    LogManagerThread.Level.INFO,
                    "PCM monitoring stopped during execution cleanup",
                )

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
            # Final PCM cleanup - ensure PCM thread is properly joined
            if pcm:
                pcm.join(
                    timeout=5
                )  # Wait up to 5 seconds for PCM thread to finish
                LogManager().log(
                    self.tool_manager.logger_name,
                    LogManagerThread.Level.INFO,
                    "PCM monitoring thread joined and cleaned up",
                )

        return exit_code
