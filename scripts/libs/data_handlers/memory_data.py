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

The `MemoryData` class is a specific implementation of the `AbstractDataHandler`
to expose the memory information of the system.
"""
from scripts.libs.data_handlers.abstract_data import AbstractDataHandler


class MemoryData(AbstractDataHandler):
    def __init__(self, args_list=None, environment_os=None) -> None:
        if not hasattr(self, "_initialized"):
            super().__init__()
            self._initialized = True
