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
Runnable Threads Package for Multi-threaded Task Execution.

This package provides a comprehensive threading framework for executing memory checking
tasks concurrently. It implements various threading strategies and patterns to maximize
performance while ensuring thread safety and proper resource management.

The package includes:

- BaseThread: Abstract base class defining the core threading interface and common
  functionality for all thread implementations. Provides thread lifecycle management,
  error handling, and synchronization primitives.

- DefaultThread: Standard thread implementation for general-purpose task execution
  with basic threading capabilities and straightforward execution patterns.

- QueueThread: Advanced thread implementation that uses queue-based task distribution
  for efficient workload management. Supports producer-consumer patterns and enables
  dynamic load balancing across multiple worker threads.

Key features:
- Thread-safe task execution with proper synchronization
- Configurable thread pools and worker management
- Queue-based task distribution for optimal load balancing  
- Exception handling and error propagation across threads
- Graceful thread shutdown and cleanup procedures
- Performance monitoring and thread utilization tracking
- Support for both CPU-bound and I/O-bound workloads

This threading framework enables the IMC tool to efficiently utilize multi-core
systems and provides scalable parallel execution capabilities for memory checking
operations across large datasets and complex system configurations.
"""
