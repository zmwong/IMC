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
IMC Plugins Package

This package defines the plugin framework for IMC memory validation tools.
It provides:
    - BasePlugin: abstract interface for all plugins, managing lifecycle and threading.
    - PCMMemoryPlugin: implementation using Intel PCM to record memory bandwidth.

Plugins follow a component-based design (SOLID) and are optimized for
cross-platform performance with minimal memory footprint.

Subpackages:
    pcm: Intel PCM memory measurement plugin
"""
