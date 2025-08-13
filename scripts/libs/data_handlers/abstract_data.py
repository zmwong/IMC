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
This module provides a base class from which all data handlers should inherit.

The `AbstractDataHandler` class defines a common interface for sharing data between
components and runnables. It uses a data dictionary to facilitate the exchange of
information during the entire execution lifecycle of a tool.
"""

from scripts.libs.utils.singleton_meta import SingletonMeta


class AbstractDataHandler(metaclass=SingletonMeta):
    """
    Base class for all data handlers.

    The `AbstractDataHandler` class provides a common interface for sharing data
    between components and runnables. It uses a data dictionary to store and share
    information, ensuring that all components have access to the same data during
    execution. This class is designed to be used as a singleton to ensure a single
    shared instance of the data dictionary.

    Attributes:
        data (dict): A dictionary used to store and share data between components
            and runnables.
    """

    def __init__(self) -> None:
        """
        Initializes the AbstractDataHandler class.

        This constructor initializes the `data` attribute as an empty dictionary,
        which will be used to store and share data between components and runnables.

        Example:
            ```
            handler = AbstractDataHandler()
            handler.data["key"] = "value"
            print(handler.data)  # Output: {'key': 'value'}
            ```
        """
        self.data = dict()
