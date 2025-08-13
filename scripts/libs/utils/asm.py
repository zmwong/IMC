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
from scripts.libs.system_handler import SystemHandler


class ASM:
    """
    A class for compiling and executing assembly code in memory.

    The `ASM` class provides functionality to allocate executable memory,
    compile machine code into callable functions, and execute or free the
    allocated memory. It wraps Windows API functions to manage memory and
    execute assembly code.

    Attributes:
        restype (ctypes type): The return type of the compiled function.
        argtypes (tuple): A tuple of argument types for the compiled function.
        machine_code (list): A list of machine code bytes to be executed.
        func (ctypes.CFUNCTYPE): A callable function pointer to the compiled code.
        address (ctypes.c_void_p): The memory address of the allocated executable memory.
        prochandle (ctypes.c_void_p): A handle to the current process.
    """

    def __init__(self, restype=None, argtypes=(), machine_code=[]):
        """
        Initializes the ASM class.

        Args:
            restype (ctypes type, optional): The return type of the compiled function.
                Defaults to `None`.
            argtypes (tuple, optional): A tuple of argument types for the compiled function.
                Defaults to an empty tuple.
            machine_code (list, optional): A list of machine code bytes to be executed.
                Defaults to an empty list.

        Example:
            ```
            asm = ASM(restype=ctypes.c_int, argtypes=(ctypes.c_int,), machine_code=[0xC3])
            ```
        """
        self.restype = restype
        self.argtypes = argtypes
        self.machine_code = machine_code
        self.func = None
        self.address = None
        self.prochandle = None

    def compile(self):
        """
        Allocates executable memory and compiles machine code into a callable function.

        This method uses Windows API functions to allocate memory, copy the machine
        code into the allocated memory, and set the memory protection to executable.
        It then creates a callable function pointer to the compiled code.

        Raises:
            Exception: If the instruction cache cannot be flushed.

        Example:
            ```
            asm = ASM(restype=ctypes.c_int, argtypes=(ctypes.c_int,), machine_code=[0xC3])
            asm.compile()
            ```
        """
        machine_code = bytes.join(b"", self.machine_code)
        self.size = ctypes.c_size_t(len(machine_code))
        if SystemHandler().os_system.platform_name == "windows":
            # Allocate a memory segment the size of the machine code, and make it executable
            size = len(machine_code)
            MEM_COMMIT = ctypes.c_ulong(0x1000)
            PAGE_READWRITE = ctypes.c_ulong(0x4)
            pfnVirtualAlloc = ctypes.windll.kernel32.VirtualAlloc
            pfnVirtualAlloc.restype = ctypes.c_void_p
            self.address = pfnVirtualAlloc(
                None, ctypes.c_size_t(size), MEM_COMMIT, PAGE_READWRITE
            )

            # Copy the machine code into the memory segment
            memmove = ctypes.CFUNCTYPE(
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_size_t,
            )(ctypes._memmove_addr)
            if memmove(self.address, machine_code, size) < 0:
                raise Exception("Failed to memmove")

            # Enable execute permissions
            PAGE_EXECUTE = ctypes.c_ulong(0x10)
            old_protect = ctypes.c_ulong(0)
            pfnVirtualProtect = ctypes.windll.kernel32.VirtualProtect
            res = pfnVirtualProtect(
                ctypes.c_void_p(self.address),
                ctypes.c_size_t(size),
                PAGE_EXECUTE,
                ctypes.byref(old_protect),
            )
            if not res:
                raise Exception("Failed VirtualProtect")

            # Flush Instruction Cache
            # First, get process Handle
            if not self.prochandle:
                pfnGetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
                pfnGetCurrentProcess.restype = ctypes.c_void_p
                self.prochandle = ctypes.c_void_p(pfnGetCurrentProcess())
            # Actually flush cache
            res = ctypes.windll.kernel32.FlushInstructionCache(
                self.prochandle,
                ctypes.c_void_p(self.address),
                ctypes.c_size_t(size),
            )
            if not res:
                raise Exception("Failed FlushInstructionCache")
        else:
            from mmap import (
                mmap,
                MAP_PRIVATE,
                MAP_ANONYMOUS,
                PROT_WRITE,
                PROT_READ,
                PROT_EXEC,
            )

            # Allocate a private and executable memory segment the size of the machine code
            machine_code = bytes.join(b"", self.machine_code)
            self.size = len(machine_code)
            self.mm = mmap(
                -1,
                self.size,
                flags=MAP_PRIVATE | MAP_ANONYMOUS,
                prot=PROT_WRITE | PROT_READ | PROT_EXEC,
            )

            # Copy the machine code into the memory segment
            self.mm.write(machine_code)
            self.address = ctypes.addressof(ctypes.c_int.from_buffer(self.mm))

        # Cast the memory segment into a function
        functype = ctypes.CFUNCTYPE(self.restype, *self.argtypes)
        self.func = functype(self.address)

    def run(self):
        """
        Executes the compiled assembly code.

        Returns:
            Any: The result of the executed function, based on the specified return type.

        Example:
            ```
            asm = ASM(restype=ctypes.c_int, argtypes=(ctypes.c_int,), machine_code=[0xC3])
            asm.compile()
            result = asm.run()
            print(result)
            ```
        """
        return self.func()

    def free(self):
        """
        Frees the allocated executable memory.

        This method uses the Windows API to release the memory allocated for the
        compiled assembly code.

        Example:
            ```
            asm = ASM(restype=ctypes.c_int, argtypes=(ctypes.c_int,), machine_code=[0xC3])
            asm.compile()
            asm.free()
            ```
        """
        if SystemHandler().os_system.platform_name == "windows":
            MEM_RELEASE = ctypes.c_ulong(0x8000)
            ctypes.windll.kernel32.VirtualFree(
                ctypes.c_void_p(self.address), ctypes.c_size_t(0), MEM_RELEASE
            )
        else:
            self.mm.close()

        self.prochandle = None
        self.mm = None
        self.func = None
        self.address = None
        self.size = 0
