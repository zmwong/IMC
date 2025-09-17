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

"""This is the test case base module which defines all of the pre-defined stress
tests."""

import os
from argparse import Namespace
from itertools import cycle, islice

from scripts.libs.utils import numa
from scripts.libs.definitions.imc import MEM_USE_DFLT

SUPPORTED_STRESS = ["upi", "ddr"]

TEST_BASE = os.path.abspath(__file__).replace(os.path.relpath(__file__), "")
TEST_BASE = (
    TEST_BASE + "ci_cd/resources/imc_tool/external_customer_tests/"
)  # LOD (imc_internal)


class StressError(Exception):
    """Custom exception class for the stress module and its commands."""


def check_test(parsed_args: Namespace) -> Namespace:
    """
    Function helper to add arguments for the stress test in the argument
    namespace.
    """
    if parsed_args.stress == "upi":
        # find all the LPUs in the nodes
        node_lpus = [
            numa.get_node_lpu(node) for node in numa.get_node_count(True)
        ]
        numa_domains = len(node_lpus)
        # check that there are enough domains to stress UPI.  There needs to be
        # at least two.
        if numa_domains < 2:
            raise StressError(
                "Unable to test UPI, there are not enough cpu domains or \
                numactl is not available."
            )

        # start the list cycle at elemnt 1
        node_cycle = islice(cycle(node_lpus), 1, None)
        for node_num in range(0, numa_domains):
            parsed_args.numa[str(node_num)] = next(node_cycle)

        # check to see if the user passed in a test case override
        if not parsed_args.xml_path:
            parsed_args.xml_path = TEST_BASE + "Test4.xml"

        # Limit the used memory to ~1GB per instance #
        # a block size of 1MB with a memory limit of 1GB appears to use 60-67%
        # of the UPI

        if parsed_args.blk_size:
            parsed_args.blk_size = 2**20  # 1MB block_size

        if parsed_args.mem_use == MEM_USE_DFLT:
            # count of the total lpus from the numa domains
            num_lpus = sum(len(lpus) for lpus in node_lpus)

            # add the total available memory from the numa domains
            free_mem = sum(
                numa.get_node_free_mem(numa_num)
                for numa_num in range(numa_domains)
            )

            # generate the percentage of memory to use based on ~1GB per
            # instance
            parsed_args.mem_use = ((2**30 * num_lpus) / free_mem) * 100

        # End limit #

        # remove any 'lpus' from the parsed_args
        parsed_args.lpus = []

    elif parsed_args.stress == "ddr":
        # Try to use numactl to ensure LPU to NUMA is strict
        # find all the LPUs in the nodes
        node_lpus = [
            numa.get_node_lpu(node) for node in numa.get_node_count(True)
        ]
        if node_lpus:
            # numactl and at least one numa domain exist
            for node_num, lpus in enumerate(node_lpus):
                parsed_args.numa[str(node_num)] = lpus
            # Clear out the default lpus
            parsed_args.lpus = []
        # check to see if the user passed in a test case override
        if not parsed_args.xml_path:
            parsed_args.xml_path = TEST_BASE + "Test2.xml"

    return parsed_args
