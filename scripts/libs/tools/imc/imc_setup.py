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

import os
from os.path import realpath, abspath, expanduser, expandvars
from scripts.libs.system_handler import SystemHandler
from scripts.libs.data_handlers.imc_data import ImcDataHandler


def _verify_imc(bin_file: str):
    """
    Verifies that the binary used is the IntelligentMemoryChecker_tool
    :param bin_file: The path to the binary file to check
    :return: True if the file is the Intelligent Memory Checker binary,
    False if not
    """
    bin_data = ""
    with open(bin_file, "rb") as imc_bin:
        bin_data = imc_bin.read()
    return bool(bin_data.find(ImcDataHandler().TOOL_NAME.encode()) != -1)


def verify_files():
    """
    Verifies that the paths provided are valid.
    """
    if not ImcDataHandler().parsed_args.imc_path:
        raise ValueError(
            f"Please provide a valid {ImcDataHandler().TOOL_NAME} path"
        )

    ImcDataHandler().parsed_args.imc_path = abspath(
        realpath(expanduser(expandvars(ImcDataHandler().parsed_args.imc_path)))
    )

    # verify that all of the paths and the imc binary are valid
    if not os.access(
        ImcDataHandler().parsed_args.imc_path, os.F_OK, follow_symlinks=True
    ):
        raise ValueError(
            f"The path to the {ImcDataHandler().TOOL_NAME} does not appear to be correct!"
        )

    if not os.access(
        ImcDataHandler().parsed_args.imc_path, os.X_OK, follow_symlinks=True
    ):
        raise ValueError(
            f"The {ImcDataHandler().TOOL_NAME} does not appear to be executable!"
        )

    if not _verify_imc(ImcDataHandler().parsed_args.imc_path):
        raise ValueError(
            f"The path '{ImcDataHandler().parsed_args.imc_path}' does not appear to be "
            + " a valid one. Please verify that this path points to "
            + f"the {ImcDataHandler().TOOL_NAME}."
        )

    for xml in ImcDataHandler().parsed_args.xml_path:
        if not os.access(xml, os.F_OK, follow_symlinks=True):
            raise ValueError(
                f"The path '{xml}' to the test case does not appear to exist!"
            )

        if not os.access(xml, os.R_OK, follow_symlinks=True):
            raise ValueError(
                f"The path to the {ImcDataHandler().TOOL_NAME} test case does not appear to be "
                "readable by the current user!"
            )
    if SystemHandler().os_system.platform_name == "windows":
        # For windows, for now, we need to check if the file ends with .exe
        if not ImcDataHandler().parsed_args.imc_path.lower().endswith(".exe"):
            raise ValueError(
                f"The {ImcDataHandler().TOOL_NAME} does not appear to be executable!"
            )
