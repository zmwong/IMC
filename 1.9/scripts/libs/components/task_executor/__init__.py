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
Task Executor Package for High-Performance Task Execution Management.

This package provides sophisticated task execution engines that orchestrate the
execution of memory checking operations across different execution models. It
implements various execution strategies optimized for different workload patterns
and system configurations.

The package includes:

- AbstractExecutor: Base abstract class defining the common interface and core
  functionality for all task executors. Provides standardized task lifecycle
  management, error handling, and performance monitoring capabilities.

- BatchExecutor: Specialized executor for batch processing operations that groups
  related tasks for efficient execution. Optimized for scenarios where tasks can
  be processed in batches to improve throughput and reduce overhead.

- QueueExecutor: Advanced executor implementing queue-based task distribution with
  dynamic load balancing and worker pool management. Ideal for high-throughput
  scenarios with varying task complexity and execution time.

Key features:
- Multiple execution strategies for different workload patterns
- Dynamic load balancing and resource allocation
- Concurrent task execution with thread pool management
- Task priority handling and scheduling optimization
- Performance monitoring and execution metrics collection
- Error handling and fault tolerance mechanisms
- Scalable architecture supporting varying system configurations
- Resource utilization optimization for memory and CPU usage

The task execution framework enables the IMC tool to efficiently scale across
different system sizes and configurations, from single-core embedded systems
to large multi-core server environments, while maintaining optimal performance
and resource utilization.
"""
