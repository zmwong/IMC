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

"""
    This is a support module for helping imc_runner find available memory and
    calculate block size.

    Ideally psutil would be used but since it's not a built-in this module
    serves many of the same features.
"""

import re
import subprocess
from typing import Union
from scripts.libs.system_handler import SystemHandler
from scripts.libs.utils.logging import init_logging, Level
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)


MAX_NUM_BLOCKS = 4096


def read_meminfo() -> dict:
    """
    Reads the /proc/meminfo and places each item into dict with the key of the
    name and the value in Bytes.
    """
    file_info = "/proc/meminfo"
    _meminfo = {}
    try:
        LoggerManager().log(
            "SYS", LoggerManagerThread.Level.DEBUG, f"Reading {file_info}"
        )
        with open(file_info, "r", encoding="utf-8") as file:
            for line in file:
                key, value, *unit = line.strip().split()
                _meminfo[re.sub(r"[\W_]+", "", key)] = int(value) * 1024
                # multiply by 1024 to convert from KB to Bytes
    except FileNotFoundError:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.CRITICAL,
            f"{file_info} was not found.",
        )
    except OSError:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.CRITICAL,
            f"{file_info} could not be read.",
        )
    except ValueError as ex_err:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.WARNING,
            f"A value in {file_info} could not be converted.",
        )
        LoggerManager().log(
            "SYS", LoggerManagerThread.Level.WARNING, str(ex_err)
        )
    return _meminfo


def get_system_info(attribute: str) -> int:
    """
    Uses systeminfo /fo csv to retrieve system information on windows
    """
    _system_info = {}
    system_info_cmd = ["systeminfo", "/FO", "CSV"]
    value = -1
    try:
        system_info = (
            subprocess.check_output(system_info_cmd).decode("utf-8").split("\r")
        )
        attr_names_list = system_info[0].split('","')
        values_list = system_info[1].split('","')
        for attr, val in zip(attr_names_list, values_list):
            _system_info[re.sub(r"[\W_]+", "", attr)] = val
        value = (
            int(_system_info.get(attribute).replace(",", "").split()[0])
            * 1024
            * 1024
        )  # convert from MB to Bytes
    except subprocess.CalledProcessError:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.CRITICAL,
            "sysinfo command could not run",
        )
    except ValueError as ex_err:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.CRITICAL,
            "A value could not be converted.",
        )
        LoggerManager().log(
            "SYS", LoggerManagerThread.Level.CRITICAL, str(ex_err)
        )
    return value


def get_svos_info(attribute: str) -> int:
    """
    Executes svosinfo command and places the values into a dictionary with their
    corresponding keys. The function will return the requested attribute and try
    to convert to bytes. Only attributes with GB values are considered.
    """
    _svos_info = {}
    svos_info_cmd = ["svosinfo"]
    value = -1
    try:
        svos_info = (
            subprocess.check_output(svos_info_cmd)
            .decode("utf-8")
            .strip()
            .split("\n")
        )
        for line in svos_info:
            if line:
                key, val = " ".join(line.split()).split("=", 1)
                _svos_info[re.sub(r"[\W_]+", "", key)] = val
        value = (
            int(float(re.findall(r"\d+\.\d+", _svos_info.get(attribute))[0]))
            * 1024
            * 1024
            * 1024
        )  # convert from GB to Bytes
    except subprocess.CalledProcessError:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.CRITICAL,
            "svosinfo command could not run",
        )
    except ValueError as ex_err:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.CRITICAL,
            "A value could not be converted.",
        )
        LoggerManager().log(
            "SYS", LoggerManagerThread.Level.CRITICAL, str(ex_err)
        )
    return value


def get_available_mem(percent: int, target=None) -> int:
    """
    Returns the total bytes of usable free memory in the system.
    """
    available_mem = 0
    if not isinstance(percent, (int, float)) or not 0 < percent <= 100:
        raise ValueError(f"{percent} is not valid for a percentage value.")
    if SystemHandler().os_system.platform_name == "windows":
        available_mem = get_system_info("AvailablePhysicalMemory") * (
            percent / 100
        )
    elif (
        SystemHandler().os_system.platform_name.lower() == "svos"
        and target is not None
    ):
        available_mem = get_svos_info("Totaltargetsystemmemory") * (
            percent / 100
        )
    else:
        available_mem = read_meminfo().get("MemAvailable") * (percent / 100)
    return available_mem  # return 0 if element isn't found


def is_swap_enabled() -> bool:
    """
    Returns True if swap is enabled False otherwise.
    """
    swap_enabled = True
    if SystemHandler().os_system.platform_name == "windows":
        swap_enabled = get_system_info("VirtualMemoryAvailable") > 0
    else:
        swap_enabled = read_meminfo().get("SwapTotal") > 0

    return swap_enabled


def check_blk_sz(
    mem_to_use: float,
    override_blk_sz: Union[int, None],
    max_blks: int = MAX_NUM_BLOCKS,
) -> int:
    """
    Checks if the 'default' block size will divide nicely into the memory to
    use.  If not a new block size is calculated.
    """

    if override_blk_sz:
        if override_blk_sz > mem_to_use:
            raise ValueError(
                f"The block size ({override_blk_sz} Bytes) cannot be larger \
                than the memory size to be tested ({mem_to_use:.2f} Bytes)."
            )
        return override_blk_sz

    ideal_blk_sz = mem_to_use / max_blks

    # List of other possible block sizes from 4kB to 4TB
    other_possible_blocks = list(
        filter(
            lambda x: int(mem_to_use / x) > 0
            and int(mem_to_use / x) <= max_blks,
            [1 << i for i in range(12, 43)],
        )
    )

    if not other_possible_blocks:
        # the memory to be tested is smaller than the smallest block size
        return int(mem_to_use)
    # closet block size to ideal from the other possible block sizes
    return min(other_possible_blocks, key=lambda x: abs(x - ideal_blk_sz))
