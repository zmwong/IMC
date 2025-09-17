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

"""
Signal Handlers Package for System Signal Management.

This package provides robust signal handling capabilities for the IMC tool, enabling
graceful handling of system signals, user interruptions, and abnormal termination
scenarios. It ensures proper cleanup and resource management when the tool receives
various system signals.

The package includes:

- DefaultHandler: Comprehensive signal handler implementation that manages common
  system signals including SIGINT (Ctrl+C), SIGTERM, SIGKILL, and other termination
  signals. Provides graceful shutdown procedures and ensures proper cleanup of
  resources, threads, and temporary files.

Key capabilities:
- Graceful handling of user interruption (Ctrl+C / SIGINT)
- Proper cleanup on termination signals (SIGTERM, SIGKILL)
- Resource cleanup and memory deallocation
- Thread termination and synchronization
- Temporary file and directory cleanup
- Log flushing and final status reporting
- Cross-platform signal handling compatibility

The signal handlers ensure that the IMC tool can respond appropriately to system
events and user actions, maintaining data integrity and system stability even
during unexpected termination scenarios. This is critical for long-running
memory checking operations that may need to be interrupted or terminated cleanly.
"""
