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
Data Handlers Package for Tool-Specific Data Management.

This package provides a comprehensive data handling framework for managing tool-specific
data throughout the execution lifecycle. It implements a singleton-based data sharing
mechanism that enables efficient communication between different components and ensures
consistent data access patterns across the entire application.

The package includes:

- AbstractDataHandler: Base abstract class that defines the common interface for all
  data handlers. Uses singleton pattern to ensure single source of truth for data
  management and provides a shared data dictionary for component communication.

- ImcDataHandler: Specialized data handler implementation for the Intelligent Memory
  Checker (IMC) tool. Manages tool-specific configuration, parsed arguments, environment
  details, logging setup, and error management infrastructure.

Key capabilities:
- Singleton-based data sharing across all components
- Tool-specific configuration and argument management
- Environment and OS details management
- Centralized logging and error handling setup
- Thread-safe data access and modification
- Lifecycle management for tool execution phases
- Integration with component initialization and cleanup

The data handlers serve as the central nervous system for tool execution, ensuring
that all components have access to the necessary configuration, state information,
and shared resources required for proper operation. This architecture promotes
loose coupling while maintaining data consistency and accessibility throughout
the tool's execution lifecycle.
"""
