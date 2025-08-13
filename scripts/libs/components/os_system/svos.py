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
# pylint: disable=line-too-long
# -*- coding: utf-8 -*-

"""
This module implements the definitions of an abstract system and specializes 
them for usage in SVOS (Scalable Virtualized Operating System).

The `SvosSystem` class extends the `LinuxSystem` class and provides a foundation
for SVOS-specific behavior. Currently, it inherits all functionality from the
Linux specialization but serves as a placeholder for future SVOS-specific
implementations.
"""

from scripts.libs.components.os_system.linux import LinuxSystem


class SvosSystem(LinuxSystem):
    """
    SVOS-specific implementation of the LinuxSystem class.

    This class provides the implementation of methods for an SVOS system. While
    it currently does not override any behavior from the `LinuxSystem` class, it
    serves as a foundation for future SVOS-specific functionality.

    Attributes:
        creation_flags (int): Flags used during process creation (inherited from `LinuxSystem`).
        safe_signal (int): The default signal used for safe termination (inherited from `LinuxSystem`).
    """

    def __init__(self) -> None:
        """
        Initializes the SvosSystem class.

        This constructor calls the parent class (`LinuxSystem`) constructor to
        initialize common attributes and functionality.

        Example:
            ```
            svos_system = SvosSystem()
            print(svos_system.creation_flags)  # Access inherited attributes
            ```
        """
        super().__init__()
        self._platform = "svos"

    @property
    def platform_name(self):
        """
        Returns the platform name identifier.

        Returns:
            str: The platform name 'svos'.
        """
        return self._platform

    @property
    def is_unix(self):
        """
        Returns whether the platform is Unix-based.

        Returns:
            bool: True as SVOS is Unix-based (derived from Linux).
        """
        return True
