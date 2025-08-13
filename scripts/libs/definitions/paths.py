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
# pylint: disable=line-too-long,expression-not-assigned
"""
These module contains different tool definitions
"""
from enum import Enum

__author__ = "Salazar, Sofia"
__copyright__ = "Copyright 2024, Intel Corporation All Rights Reserved."
__license__ = "Confidential"
__version__ = "0.1"
__status__ = "Development"


class DefaultPaths:
    GENERATED_TESTS = "resources/generated/"
    BASIC_TEST = "resources/basic_imc_test_case.xml"
    GENERIC_TEST = "resources/generic_imc_test_case.xml"
    COMPILED_TOOL_BINARY = "/build/IntelligentMemoryChecker/"
    INSTALLED_DPKG = "/usr/bin/"
    PREFERENCES = "/imcCompilingPreferences.json"
    BUILD = "/build"
    OLD_BUILD = "/old_compilations"
    BUILD_SYSTEM = "/build_system"
    CMAKE_DEBIAN_PACKAGE = "/Makefile.am"
    CMAKELISTS = "/CMakeLists.txt"
    CMAKE_LIBRARY = "/CMakeLists.shared.library.txt"
    CMAKE_SCRIPT = "/CMakeLists.script.txt"
    DPKG = "/Debian-Package-files-generated"
    LICENSES = "/licenses"
