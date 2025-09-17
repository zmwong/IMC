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
    This is a support module for helping imc_runner find determine the numa
    nodes and the memory associated with each node.
    sysfs is required for this to function correctly.

"""
import re
import subprocess  # nosec
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)

from .logging import init_logging, Level


def numactl_available() -> bool:
    """
    Checks the system to see if numactl is installed.

    :return: bool
    """
    try:
        subprocess.run(
            ["numactl", "-s"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=True,
        )  # nosec
        return True
    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
    ):
        return False


def _read_file(path: str) -> list:
    """
    A helper function to read the files from /sys/devices/system/node/*
    :param path: a path to the file to read
    :return: a list of the lines read from the file.
    """
    file_info = "/sys/devices/system/node" + path
    read_lines = []
    try:

        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.DEBUG,
            f"{file_info} was not found.",
        )
        with open(file_info, "r", encoding="utf-8") as file:
            read_lines = file.read().splitlines()
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
    return read_lines


def get_node_meminfo(numanode: int) -> dict:
    """
    Reads the /sys/devices/system/node/node{numanode}/meminfo and places each
    item into a dict with its corresponding value.
    The dict containing all of the meminfo is returned.
    :param numanode: an int of the selected numa
    :return: dict of the meminfo
    """
    file_info = f"/node{numanode}/meminfo"
    _meminfo = {}
    try:
        for line in _read_file(file_info):
            LoggerManager().log(
                "SYS",
                LoggerManagerThread.Level.DEBUG,
                f"Parsing line of data: {line}",
            )
            key, value, *unit = re.sub(
                r"Node [0-9]+ |[^\w()]+", " ", line
            ).split()
            if unit and unit[0] == "mB":
                _meminfo[key] = int(value) * 2**20
            elif unit and unit[0] == "kB":
                _meminfo[key] = int(value) * 2**10
            else:
                _meminfo[key] = int(value)
    except ValueError as ex_err:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.WARNING,
            f"A value in {file_info} could not be converted.",
        )
        LoggerManager().log("SYS", LoggerManagerThread.Level.WARNING, ex_err)
        LoggerManager().log("SYS", LoggerManagerThread.Level.WARNING, line)

    return _meminfo


def get_node_free_mem(numanode: str = None) -> int:
    """Helper to get the free memory of a node from the node meminfo
    :param numanode: a str number of the selected numa
    :return: int value of the free memory from meminfo
    """
    try:
        return get_node_meminfo(int(numanode))["MemFree"]
    except ValueError:
        return 0


def get_node_lpu(numanode: int) -> list:
    """
    Reads the /sys/devices/system/node/node{numanode}/cpulist and returns a list
    of the LPUs for this numa node.
    :param numanode: an integer of the numa number
    :return: list of the lpus in the selected numa node
    """
    file_info = f"/node{numanode}/cpulist"
    lpu_list = []
    try:
        for line in _read_file(file_info):
            LoggerManager().log(
                "SYS",
                LoggerManagerThread.Level.DEBUG,
                f"Parsing line of data: {line}",
            )
            for cpus in line.split(","):
                start_lpu, *end_lpu = cpus.split("-")
                if end_lpu:
                    lpu_list.extend(
                        list(range(int(start_lpu), int(end_lpu[0]) + 1))
                    )
                else:
                    lpu_list.append(int(start_lpu))
    except ValueError as ex_err:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.WARNING,
            f"A value in {file_info} could not be converted.",
        )
        LoggerManager().log("SYS", LoggerManagerThread.Level.WARNING, ex_err)

    return lpu_list


def get_node_count(check_numactl: bool = False) -> list:
    """
    Reads the /sys/devices/system/node/online list of nodes and returns a list
    of the numa node number.
    :return: list of the numa nodes ids
    """
    if check_numactl and not numactl_available():
        return []
    file_info = "/online"
    numa_list = []
    try:
        for line in _read_file(file_info):
            start_numa, *end_numa = line.split("-")
            if end_numa:
                numa_list.extend(
                    list(range(int(start_numa), int(end_numa[0]) + 1))
                )
            else:
                numa_list.append(int(start_numa))
    except ValueError as ex_err:
        LoggerManager().log(
            "SYS",
            LoggerManagerThread.Level.WARNING,
            f"A value in {file_info} could not be converted.",
        )
        LoggerManager().log("SYS", LoggerManagerThread.Level.WARNING, ex_err)

    return numa_list


def get_all_lpus() -> list:
    """
    A helper function that returns a list of the numa Node number with its LPUs
    :return: List of Nodes with their LPUs
    """
    nodes = []
    for node in get_node_count():
        nodes.insert(node, get_node_lpu(node))
    return nodes
