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

from abc import abstractmethod

"""
This module provides the abstract definition of a runnable.
"""


class AbstractRunnable:
    """
    An interface for implementing the runnable for a tool.

    A runnable is an object composed of different components with the purpose of
    executing multiple instances of a tool. This interface allows for the use of a
    common interface when executing the different tools throught the override of the
    execute method.
    """

    @abstractmethod
    def generate_command(*args, **kwargs):
        """
        Implement this method to generate the command to execute the tool.
        """
        pass

    # @staticmethod/
    # @abstractmethod
    def parse_args_list(args_list):
        """
        Implement to implement the specific parsing of a tool's args list.
        """
        pass

    @abstractmethod
    def setup(self):
        """
        Implement this method to add the necessary setup for your tool, previous to
        execution.
        """
        pass

    @abstractmethod
    def execute(self):
        """
        Implement this method to the specific execution requirements of your tool.
        """
        pass

    @abstractmethod
    def post(self):
        """
        Implement this method to implement behaviours post execution of your tool.
        """
        pass
