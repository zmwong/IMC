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
Factories Package for Object Creation and Dependency Injection.

This package implements the Factory design pattern to provide a scalable and flexible
way of creating complex objects and managing their dependencies. It enables loose
coupling between components by abstracting the object creation process and supporting
dynamic component assembly.

The package includes:

- RunnableFactory: Factory for creating runnable objects with proper dependency injection
  and lazy loading capabilities. Handles the creation of IMC runnable instances with
  all necessary components configured and ready for execution.

The factory pattern implementation supports:
- Lazy loading of components to improve startup performance
- Dynamic configuration of object dependencies
- Centralized object creation logic for better maintainability
- Support for different runnable types and configurations

This approach enables the IMC tool to maintain flexible architecture while ensuring
proper component initialization and dependency management.
"""
