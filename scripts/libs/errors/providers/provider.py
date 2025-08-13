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
# pylint: disable=missing-function-docstring

""" This module defines the base provider class that must be overridden. """


class BaseProvider:
    """Base Error Provider interface"""

    def __init__(self, path: str = None):
        self.path = path

    def _self_test(self):
        raise NotImplementedError()

    def init(self):
        raise NotImplementedError()

    def get_errors(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()
