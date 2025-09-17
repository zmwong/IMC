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
Distributions Package for Command Generation Strategies.

This package provides various command distribution strategies for generating and managing
test commands in the IMC tool. It implements different algorithms for distributing
workloads and creating command sequences that can be executed across different
system configurations.

The package includes:

- AbstractDistribution: Base class defining the interface for all distribution strategies
- CycleDistribution: Implementation for cyclic command generation patterns

These distributions enable flexible command generation strategies that can be adapted
to different testing scenarios, workload patterns, and system requirements. The abstract
base class ensures consistent behavior while allowing for specialized implementations
that can optimize command generation for specific use cases.
"""
