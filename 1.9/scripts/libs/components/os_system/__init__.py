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
OS System Package for Cross-Platform Operating System Abstraction.

This package provides a comprehensive abstraction layer for operating system specific
functionality, enabling the IMC tool to run consistently across different platforms
including Linux, Windows, and specialized operating systems like SVOS. It implements
the Strategy pattern to provide platform-specific implementations behind a common interface.

The package includes:

- AbstractSystem: Base abstract class defining the common interface for all OS implementations
- Linux: Linux-specific system implementation with support for NUMA, process management,
  and Linux-specific memory checking capabilities
- Windows: Windows-specific system implementation for Windows environments
- SVOS: Specialized implementation for SVOS (Specialized Virtualized Operating System)
- NumaGeneration: NUMA (Non-Uniform Memory Access) topology detection and management

Key capabilities:
- Cross-platform process and thread management
- CPU instruction set detection and validation
- Process priority control and affinity settings
- NUMA topology detection and memory allocation strategies
- Platform-specific command generation and execution
- Safe thread termination and cleanup procedures
- Memory architecture detection and optimization

This abstraction enables the IMC tool to leverage platform-specific optimizations
while maintaining a consistent interface across all supported operating systems,
ensuring reliable memory checking capabilities regardless of the target platform.
"""
