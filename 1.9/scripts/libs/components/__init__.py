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
Components Package for Intelligent Memory Checker (IMC) Tool.

This package contains the core components and building blocks used throughout the IMC tool
architecture. It provides modular, reusable components that handle various aspects of the
system including task execution, thread management, signal handling, OS system abstraction,
logging, factory patterns, and command distribution strategies.

The components package is organized into the following subpackages:

- distributions: Command distribution strategies for generating and managing test commands
- factories: Factory pattern implementations for creating runnable objects and components  
- loggers: Logging management and configuration utilities
- os_system: Operating system abstraction layer for cross-platform compatibility
- runnable_threads: Thread management and execution components
- signal_handlers: Signal processing and handling utilities
- task_executor: Task execution engines and batch processing components

Each subpackage provides specialized functionality while maintaining loose coupling and
high cohesion, enabling flexible composition and testing of the IMC tool's capabilities.
"""
