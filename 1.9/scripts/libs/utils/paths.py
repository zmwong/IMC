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
This module contains path related functions.
"""
import os
from os.path import isfile, join

from scripts.libs.definitions.paths import DefaultPaths
from scripts.libs.definitions.imc import BinaryNames

__author__ = "Salazar, Sofia"
__copyright__ = "Copyright 2024, Intel Corporation All Rights Reserved."
__license__ = "Confidential"
__version__ = "0.1"
__status__ = "Development"


def verify_binary_exists(imc_path):
    """Write affected files paths on log.
    :return: None
    """
    bin_path = DefaultPaths.COMPILED_TOOL_BINARY + BinaryNames.REGULAR_BINARY
    ver_path = DefaultPaths.COMPILED_TOOL_BINARY + BinaryNames.VERSION_BINARY

    if not os.access(imc_path, os.F_OK, follow_symlinks=True):
        print("The path to IMC does not appear to be correct!")
    elif not os.access(imc_path, os.X_OK, follow_symlinks=True):
        print("The path does not appear to be executable!")
    else:
        return imc_path
    if os.path.exists(bin_path):
        print("Default build binary exists!")
        return bin_path
    elif os.path.exists(ver_path):
        print("Default build binary with version exists!")
        return ver_path
    else:
        return None  # Was not able to find any binary at default paths


def fix_full_path(directory):
    fixed_path = os.path.abspath(os.getcwd()) + directory
    return fixed_path


def get_subdirs(dirname):
    """Retrieves all subdirectories recursively

    :return: List
    """
    subfolders = []
    if os.path.isdir(dirname):
        subfolders = [f.path for f in os.scandir(dirname) if f.is_dir()]
        for dirname in list(subfolders):
            subfolders.extend(get_subdirs(dirname))
        subfolders.sort()
    return subfolders


def get_files(dirname, file_extension=""):
    """Retrieves all files with full path.

    :return: List
    """
    files_names = sorted(
        [
            os.path.join(dirname, f)
            for f in os.listdir(dirname)
            if isfile(join(dirname, f)) and f.endswith(file_extension)
        ]
    )
    return files_names


def check_make_dir(path):
    """Creates logs directory and file if does not exist.

    :return: status
    """
    if not os.path.isdir(path):
        os.makedirs(path)


def get_files_filter_name(files, names_to_filter):
    """Retrieves all files except those which match file_name

    return: List
    """
    for filename in files:
        # If matches the file name, pop it from the list
        if filename in names_to_filter:
            files.remove(filename)
            continue
    files.sort()
    return files


def get_dirs(dirname):
    """Retrieves all subdirectories recursively

    :return: List
    """
    subfolders = []
    if os.path.isdir(dirname):
        subfolders = [f.path for f in os.scandir(dirname) if f.is_dir()]
        for dirname in list(subfolders):
            subfolders.extend(get_dirs(dirname))
        subfolders.sort()
    return subfolders


def run_fast_scandir(dir, ext=""):  # dir: str, ext: list
    subfolders, files = [], []
    subfolders = get_dirs(dir)
    subfolders.insert(0, dir)
    for folder in subfolders:
        files += get_files(folder, ext)
    return files  # Add a subfolders return if needed (subfolders, files)


def fix_full_path_from_root(directory):
    root_path = os.environ.get("PROJECT_ROOT")
    if root_path is not None:
        fixed_path = os.path.abspath(root_path) + directory
    else:
        fixed_path = fix_full_path(directory)

    return os.path.normcase(fixed_path)
