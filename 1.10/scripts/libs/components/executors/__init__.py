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
Task Executor and Threading Framework for Task Execution.

This package provides a comprehensive framework for managing and executing memory
checking tasks concurrently. It combines sophisticated task execution engines with
a versatile threading model to maximize performance, scalability, and resource
utilization across various system configurations.

The framework includes:

- **Task Executors**: Orchestrate memory checking operations using different
  execution strategies optimized for various workloads.
  - `AbstractExecutor`: A base class defining a common interface for all task
    executors, ensuring standardized lifecycle management and error handling.
  - `BatchExecutor`: A specialized executor for grouping and processing tasks in
    batches, enhancing throughput and reducing overhead.
  - `QueueExecutor`: An advanced executor that uses queue-based task distribution
    for dynamic load balancing and efficient worker pool management.

- **Threading Components**: A set of threading implementations for concurrent
  task execution.
  - `BaseThread`: An abstract base class that defines the core interface and
    common functionality for all thread implementations.
  - `DefaultThread`: A standard thread implementation for general-purpose tasks.
  - `QueueThread`: An advanced thread that works with queue-based task
    distribution, ideal for producer-consumer patterns.

Key Features:
- Multiple execution strategies for diverse workload patterns.
- Thread-safe task execution with robust synchronization.
- Queue-based task distribution for optimal load balancing.
- Dynamic resource allocation and configurable thread pools.
- Comprehensive performance monitoring and execution metrics.
- Graceful thread shutdown, exception handling, and fault tolerance.
- Scalable architecture for single-core, multi-core, and distributed systems.

This integrated framework enables the IMC tool to achieve efficient, scalable,
and parallel execution of memory checking operations, ensuring optimal performance
from embedded systems to large-scale server environments.
"""
