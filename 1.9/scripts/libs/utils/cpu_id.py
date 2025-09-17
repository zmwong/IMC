#!/usr/bin/python
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

import ctypes
from scripts.libs.utils.asm import ASM


class CPUID:
    """
    A utility class for executing CPUID instructions and retrieving CPU flags.

    The `CPUID` class uses the `ASM` class to execute low-level assembly instructions
    and retrieve information about the CPU's supported instruction sets.

    Methods:
        _run_asm(*machine_code): Executes assembly instructions and retrieves register values.
        get_flags(): Retrieves supported CPU instruction sets by analyzing specific register bits.
    """

    def __init__(self):
        """
        Initializes the CPUID class.

        Example:
            ```
            cpuid = CPUID()
            ```
        """
        pass

    def _run_asm(self, *machine_code):
        """
        Executes assembly instructions using the ASM class.

        This method compiles and executes the provided machine code using the [ASM](http://_vscodecontentref_/1) class
        and retrieves the value of the `EAX` register.

        Args:
            *machine_code (bytes): Variable-length arguments representing the machine code
                instructions to execute.

        Returns:
            int: The value of the `EAX` register after executing the instructions.

        Example:
            ```
            cpuid = CPUID()
            eax_value = cpuid._run_asm(
                b"\\xB8\\x01\\x00\\x00\\x00",  # mov eax,0x1
                b"\\x0f\\xa2",                # cpuid
                b"\\x89\\xD0",                # mov eax,edx
                b"\\xC3"                      # ret
            )
            print(eax_value)
            ```
        """
        asm = ASM(ctypes.c_uint32, (), machine_code)
        asm.compile()
        retval = asm.run()
        asm.free()
        return retval

    def get_flag_dynamic(self, leaf, subleaf):
        """
        Executes CPUID for the given leaf and subleaf once and returns all registers.

        Returns:
            dict: {'eax': eax, 'ebx': ebx, 'ecx': ecx, 'edx': edx}
        """
        eax = self._run_asm(
            b"\xB8" + leaf.to_bytes(4, "little"),
            b"\xB9" + subleaf.to_bytes(4, "little"),
            b"\x0F\xA2",  # cpuid
            b"\x89\xC0",  # mov eax, eax
            b"\xC3",  # ret
        )
        ebx = self._run_asm(
            b"\xB8" + leaf.to_bytes(4, "little"),
            b"\xB9" + subleaf.to_bytes(4, "little"),
            b"\x0F\xA2",
            b"\x89\xD8",  # mov eax, ebx
            b"\xC3",
        )
        ecx = self._run_asm(
            b"\xB8" + leaf.to_bytes(4, "little"),
            b"\xB9" + subleaf.to_bytes(4, "little"),
            b"\x0F\xA2",
            b"\x89\xC8",  # mov eax, ecx
            b"\xC3",
        )
        edx = self._run_asm(
            b"\xB8" + leaf.to_bytes(4, "little"),
            b"\xB9" + subleaf.to_bytes(4, "little"),
            b"\x0F\xA2",
            b"\x89\xD0",  # mov eax, edx
            b"\xC3",
        )
        return {"eax": eax, "ebx": ebx, "ecx": ecx, "edx": edx}
