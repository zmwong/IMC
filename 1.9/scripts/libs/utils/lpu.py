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
    This module is a helper utility to gather the Logical Processing Unit
    information.
"""
import os
import re
import logging
import multiprocessing

_logger = logging.getLogger(__package__)


def get_lpu_count() -> int:
    """Attempts to use the multiprocessing module to get the number of logical
    processors.  If it raises NotImplementedError then Python was unable to
    determine the number of processors in the system.

    :return: int
    """
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 0


def get_lpu_list() -> tuple:
    """Returns a tuple list of lpus for the OS in use."""
    if os.name == "nt":
        start = 0
    elif os.name == "posix":
        start = 0
    else:
        # the starting lpu is unknown so we'll start 1 from the end
        start = get_lpu_count() - 1
        _logger.warning(
            "Unable to determine starting logical processing unit number.\
            Defaulting to %s",
            start,
        )
    return tuple(range(start, get_lpu_count()))


def expand_lpu_string(lpu_string: str) -> list:
    """
    Expands the provided LPU string and returns a set containing all unique
    entries

    Example expansion:1,2,3:5,6-12 -> 1,2,3:5,6:12 -> 1,2,3,4,5,6,7,8,9,10,11,12

    :param lpu_string: String containing a list of LPUs.
    If None is provided then all discovered lpus will be returned.
    :return: list
    """
    lpu_list = set()
    if lpu_string is None:
        return get_lpu_list()

    # matches 1:n or 1-n in three groups 1,:,n or matches a unsigned value
    re_string = r"((^\d+)(-)(\d+))|((^\d+)(\:)(\d+))|(^\d+)*$"
    re_prog = re.compile(re_string)
    lpu_string = lpu_string.replace(" ", "")
    for cpu_num in lpu_string.split(","):
        re_match = re_prog.match(cpu_num)
        if re_match:
            lpu_range = [
                int(x) for x in re_match.group(2, 4, 6, 8) if x
            ]  # hyphen or colon groups
            if re_match.group(3) or re_match.group(
                7
            ):  # hyphen or colon group found
                if lpu_range[0] > lpu_range[1]:
                    _logger.warning(
                        "LPU range {0}-{1} is invalid, did you mean {1}-{0}?",
                        *lpu_range
                    )
                lpu_list = lpu_list.union(range(lpu_range[0], lpu_range[1] + 1))
            elif re_match.group(9):  # lonely digits club
                lpu_list.add(int(re_match.group()))
            else:
                lpu_list.add(re_match.group())
        else:
            # This will be bogus but it'll be caught later
            lpu_list.add(cpu_num)

    new_list = []
    available_lpus = get_lpu_list()
    for lpu in lpu_list:
        if lpu not in available_lpus:
            _logger.error(
                "Skipping LPU %s because it does not appear to exist.", lpu
            )
            continue
        new_list.append(lpu)

    return new_list
