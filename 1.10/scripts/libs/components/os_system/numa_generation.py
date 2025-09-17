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
This module implements the definitions for NUMA (Non-Uniform Memory Access) platforms.

It is used for command generation and is coupled with an OS system that provides
the specific implementation. The `NumaHandler` class provides methods to generate
commands for running test cases on NUMA platforms.
"""

from scripts.libs.utils import mem
from scripts.libs.system_handler import SystemHandler
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


class NumaHandler:
    """
    A handler for generating commands for NUMA platforms.

    This class provides methods to generate commands for running test cases
    on NUMA platforms, taking into account memory allocation, logical processing
    units (LPUs), and NUMA node bindings.

    Attributes:
        tool_manager (object): An object responsible for managing tool-specific data and operations.
    """

    def __init__(self, tool_manager) -> None:
        """
        Initializes the NumaHandler class.

        Args:
            tool_manager (object): An object responsible for managing tool-specific data and operations.
        """
        self.tool_manager = tool_manager

    def generate_command(
        self, test_case: str, mem_per_instance: float, lpu: int, numa_num: int
    ) -> list:
        """
        Generates a command to run the test case with the given parameters using NUMA.

        This method creates a command that binds the process to a specific NUMA node
        and logical processing unit (LPU), allocates memory, and sets the block size
        for the test case.

        Args:
            test_case (str): The path to the test case XML file.
            mem_per_instance (float): The amount of memory allocated per instance (in bytes).
            lpu (int): The logical processing unit (LPU) to bind the process to.
            numa_num (int): The NUMA node to bind the memory allocation to.

        Returns:
            list: A list representing the full command to execute the test case.

        Example:
            ```
            from scripts.libs.tool.tool_manager import ToolManager
            # Initialize tool manager with required configuration
            tool_manager = ToolManager(parsed_args, environment, logger)
            # Create NUMA handler with tool manager
            numa_handler = NumaHandler(tool_manager)
            # Generate command with specified parameters
            command = numa_handler.generate_command(
                "test_case.xml", 1048576, 2, 0
            )
            print(command)
            # Output:
            # ['nice', '-n', '0', 'numactl', '--membind=0', '--physcpubind=2',
            #  '/path/to/imc', 'test_case.xml', '-m', '1048576', '-b', '4096']
            ```

        Raises:
            ValueError: If the block size cannot be determined or is invalid.
        """
        exec_path = [
            self.tool_manager.tool_data.parsed_args.imc_path,
            self.tool_manager.tool_data.parsed_args.xml_path,
        ]

        # Determine the block size if not already set
        if not self.tool_manager.tool_data.parsed_args.blk_size:
            self.tool_manager.tool_data.parsed_args.blk_size = mem.check_blk_sz(
                mem_per_instance,
                self.tool_manager.tool_data.parsed_args.blk_size,
            )
        blk_size_str = f"block size of {self.tool_manager.tool_data.parsed_args.blk_size} bytes"
        LogManager().log(
            "SYS",
            LogManagerThread.Level.DEBUG,
            f"Using {self.tool_manager.tool_data.parsed_args.mem_use:.2f}% of available memory, with a {blk_size_str}.",
        )

        # Generate the command
        _cmd = SystemHandler().os_system.set_priority(
            self.tool_manager.tool_data.parsed_args.priority
        ) + [
            "numactl",
            f"--membind={numa_num}",
            f"--physcpubind={lpu}",
        ]
        exec_path[1] = test_case
        _cmd.extend(exec_path)
        _cmd.extend(["-m", str(int(mem_per_instance))])
        if self.tool_manager.tool_data.parsed_args.blk_size:
            _cmd.extend(
                ["-b", str(self.tool_manager.tool_data.parsed_args.blk_size)]
            )
        return _cmd
