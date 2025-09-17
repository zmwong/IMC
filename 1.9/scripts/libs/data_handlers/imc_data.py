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
This module provides the specific definitions for the data handling in the IMC tool.

The `ImcDataHandler` class is a specific implementation of the `AbstractDataHandler`
for the Intelligent Memory Checker (IMC) tool. It initializes the logger, error
manager, and other components required for the tool's execution.
"""

from scripts.libs.data_handlers.abstract_data import AbstractDataHandler


class ImcDataHandler(AbstractDataHandler):
    """
    Data handler for the Intelligent Memory Checker (IMC) tool.

    This class initializes the logger, error manager, and other components
    required for the IMC tool. It also parses the command-line arguments and
    sets up automated tests.

    Attributes:
        parsed_args (argparse.Namespace): Parsed command-line arguments for the IMC tool.
        environment_os (object): The operating system environment details.
        TOOL_NAME (str): The name of the tool ("Intelligent Memory Checker").
        LOGGER (logging.Logger): The logger instance for the tool.
        mgr (ErrorManager): The error manager instance for handling errors.
    """

    def __init__(self, parsed_args) -> None:
        """
        Initializes the ImcDataHandler class.

        Args:
            parsed_args (namespace): A namespace containing the parsed arguments of IMC.

        Raises:
            ErrorProviderNotFound: If the specified error provider is not found.
            stress.StressError: If there is an error during the setup of automated tests.

        Example:
            ```
            args = ["--verbosity", "2", "--provider", "Auto"]
            handler = ImcDataHandler(args, environment)
            print(handler.TOOL_NAME)  # Output: "Intelligent Memory Checker"
            ```
        """
        super().__init__()
        self.parsed_args = parsed_args
        self.TOOL_NAME = "Intelligent Memory Checker"
