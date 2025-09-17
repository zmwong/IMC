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
Runnables Package for Tool Execution Orchestration.

This package provides the core execution framework for tool orchestration and
lifecycle management. It defines the abstract interfaces and concrete implementations
for executing multiple instances of tools with proper component composition and
coordination.

The package includes:

- AbstractRunnable: Base abstract interface that defines the common contract for
  all runnable implementations. Provides the foundation for tool execution with
  standardized lifecycle methods and component integration patterns.

- DefaultRunnable: Specialized runnable implementation for the Intelligent Memory Checker
  (IMC) tool. Orchestrates the execution of memory checking operations by coordinating
  various components including task executors, distribution strategies, thread
  management, and tool managers.

- StressVariableRunnable: Advanced runnable implementation that provides variable stress
  patterns using sine wave modulation. Extends the default behavior with dynamic thread
  management to create fluctuating memory stress levels for more realistic testing
  scenarios.

Key capabilities:
- Standardized tool execution interface and lifecycle management
- Component composition and dependency injection
- Multi-instance tool execution with proper resource management
- Integration with task executors and distribution strategies
- Thread management and parallel execution coordination
- Tool manager integration for specific tool implementations
- Error handling and graceful shutdown procedures
- Performance monitoring and execution metrics collection

The runnable framework enables the IMC tool to execute complex memory checking
workflows while maintaining clean separation of concerns between execution
orchestration and specific tool logic. This architecture supports scalable
execution across different system configurations and enables flexible composition
of execution strategies and components.
"""
