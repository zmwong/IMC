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
This module provides an abstract base class for defining command distributions. It serves as a 
foundation for implementing specific command generation strategies for tools. The module includes 
an abstract method that must be implemented by subclasses and a utility method for expanding 
command lists.

Classes:
    AbstractDistribution: An abstract base class that defines the structure and behavior for 
    command distributions.

Usage:
    Subclass AbstractDistribution and implement the `generate_commands` method to define 
    custom command generation logic.

Raises:
    NotImplementedError: If the `generate_commands` method is not implemented by a subclass.
    ValueError: If the `expand_cmd_list` method is called with an empty `original_list`.
"""
from abc import ABC
from abc import abstractmethod


class AbstractDistribution(ABC):
    """
    This abstract base class provides a foundation for implementing command distributions.
    It defines the structure and behavior that subclasses must adhere to, including the
    requirement to implement the `generate_commands` method.

    Attributes:
        tool_manager (object): An object responsible for managing tool-specific data and operations.
                              Contains tool_data and methods for command generation.

    Methods:
        generate_commands():
            Abstract method that must be implemented by subclasses to generate commands.

        expand_cmd_list(original_list, required_size):
            Expands a list of commands to a specified size by reusing elements from the
            original list.

    Raises:
        NotImplementedError: Raised if the `generate_commands` method is not implemented
        by a subclass.
        ValueError: Raised if the `expand_cmd_list` method is called with an empty
        `original_list`.
    """

    def __init__(self, tool_manager) -> None:
        """
        Initializes the AbstractDistribution with a tool manager.

        Args:
            tool_manager (object): An object responsible for managing tool-specific data and operations.
                                  Contains tool_data and methods for command generation.
        """
        super().__init__()
        self.tool_manager = tool_manager

    @abstractmethod
    def generate_commands(self):
        """
        Abstract method to generate commands.

        This method must be implemented by subclasses to define the logic for generating
        commands specific to a tool or use case. The implementation should use the tool_manager
        to access tool data and command generation methods.

        Returns:
            list: A list of commands to be executed.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        return

    @staticmethod
    def expand_cmd_list(original_list, required_size):
        """
        Expands a list of commands to a specified size by reusing elements from the original list.

        This method ensures that the resulting list has the required size by repeatedly
        appending elements from the original list until the desired size is reached. If the
        original list is already larger than or equal to the required size, it is returned as is.

        Args:
            original_list (list): The list of commands to be expanded.
            required_size (int): The desired size of the expanded list.

        Returns:
            list: A list of commands expanded to the required size.

        Raises:
            ValueError: If the `original_list` is empty.
        """
        if not original_list:
            raise ValueError("The command list cannot be empty")

        if len(original_list) >= required_size:
            return original_list
        expanded_list = []
        while len(expanded_list) < required_size:
            expanded_list.extend(original_list)

        return expanded_list[:required_size]
