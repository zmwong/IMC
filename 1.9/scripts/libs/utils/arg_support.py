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
This module assists the argparse ArgumentParser to add additional functionality.
"""

import os
import re
import argparse
import re
from os.path import realpath, abspath, expanduser, expandvars
import scripts.libs.utils.paths as paths
from scripts.libs.utils.lazy_loader import LazyLoader
from scripts.libs.test_generator import generator_parser
from scripts.libs.utils.lpu import expand_lpu_string


def int_safely(val: str):
    """A method to cast a string to int and handle the thrown exception"""
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


class StressAction(argparse.Action):
    """Helper class for the stress command line argument.  Works around the
    required positional argument for the XML test case."""

    # pylint: disable=too-few-public-methods

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings=option_strings, dest=dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None, **kwargs):
        setattr(namespace, self.dest, values)
        # remove the 'required' positional argument to prevent argparse from
        # raising a failure if --stress is provided
        parser._actions = [
            action for action in parser._actions if action.option_strings
        ]


class VerboseAction(argparse.Action):
    """Helper class for verifying the verbosity values.  This has the same
    functionality as argparse._CountAction but supports nargs for 'off'."""

    # pylint: disable=too-few-public-methods
    # there are only 6 levels of verbosity; OFF, CRITICAL, ERROR, WARNING,
    # INFO, DEBUG
    max_verbosity = 5  # considering a range from 0 to 5

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(
            option_strings=option_strings, dest=dest, nargs="?", **kwargs
        )

    def __call__(self, parser, namespace, values, option_string=None, **kwargs):
        msg = "The verbosity level provided is invalid"
        if values is None:
            values = 1
        elif len(values) >= self.max_verbosity:
            raise argparse.ArgumentError(self, msg)
        elif isinstance(int_safely(values), int):
            int_val = int_safely(values)
            # Only consider values from 0 to 5
            if int_val not in range(0, self.max_verbosity + 1):
                raise argparse.ArgumentError(self, msg)
            values = int_val
        elif values.lower() == "off":
            values = 0
        elif not all(x == option_string[1] for x in values):
            raise argparse.ArgumentError(self, msg)
        else:
            values = max(
                0, min(values.count(option_string[1]) + 1, self.max_verbosity)
            )

        setattr(namespace, self.dest, values)


class NumaLpuAction(argparse.Action):
    """An argparse action class used by the --lpus and --numaX arguments to find
    the numa or lpus."""

    # pylint: disable=too-few-public-methods

    def __call__(self, parser, namespace, values, option_string=None):
        # arguments lpus and numa are mutually exclusive - raise an error if
        # they are both used
        # the reason add_mutually_exclusive_group() is not used is because
        # multiple numa destinations are supported
        msg = "{} argument cannot be used in combination with {} argument"
        if getattr(namespace, "lpus") and self.dest == "numa":
            raise argparse.ArgumentError(self, msg.format("numa", "lpus"))
        if (
            hasattr(namespace, "numa")
            and getattr(namespace, "numa")
            and self.dest == "lpus"
        ):
            raise argparse.ArgumentError(self, msg.format("lpus", "numa"))

        # find the destination in the namespace otherwise set an empty dict
        items = getattr(namespace, self.dest) or {}
        lpus = expand_lpu_string(values)
        if len(lpus) <= 0:
            raise argparse.ArgumentError(
                self,
                "No lpus were found. Please check the lpu number(s) and try again",
            )

        if self.dest == "numa":
            numa_num = int(option_string[-1:])
            items[str(numa_num)] = lpus
        else:
            items = lpus  # override the dict and use the lpu list

        setattr(namespace, self.dest, items)


def mem_value_type(use_value: str) -> int:
    """
    An argparse function used to check the memory value provided by the user.
    """
    try:
        use_value = float(use_value.strip("%"))
        if use_value <= 0 or use_value > 100:
            raise ValueError
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            "Memory value should be a percentage >0% and <=100%"
        ) from err
    return use_value


def timeout_type(timeout_min: str) -> int:
    """
    An argparse function to check the timeout value provided by the user.
    """
    timeout_limit = 10080  # time limit of 1 week in minutes
    try:
        timeout_min = float(timeout_min)
        if timeout_min < 0 or timeout_min > timeout_limit:
            raise ValueError
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            f"Timeout value should be between 0 and {timeout_limit} minutes"
        ) from err
    return timeout_min


def time_type(time_sec: str) -> int:
    """
    An argparse function to check the execution time value provided by the user.
    The input should be a time value in seconds
    """
    timeout_limit = 604800  # execution time limit of 1 week in seconds
    try:
        time_sec = int(time_sec)
        if time_sec <= 0 or time_sec > timeout_limit:
            raise ValueError
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            f"Timeout value should be between 1 and {timeout_limit} seconds"
        ) from err
    return time_sec


def priority_type(value: str):
    """Verifies that the value entered is a number between 0 and 100."""
    try:
        value = int(value)
        if value > 100 or value < 0:
            raise ValueError
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            "Priority value should be between 0 and 100"
        ) from err
    return value


class CheckCsvAction(argparse.Action):
    """Helper class to check the CSV file. If exists, create dictionary."""

    # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        # exand the real path to the csv
        values = abspath(realpath(expanduser(expandvars(values))))
        if not os.access(values, os.F_OK, follow_symlinks=True):
            raise argparse.ArgumentError(
                self,
                f"The path '{values}' does not appear to exist. "
                + "Enter a valid one.",
            )
        data_source = generator_parser.read_csv(values)
        # set the value in the parser
        setattr(namespace, self.dest, data_source)


class CheckPathsAction(argparse.Action):
    """Helper class to check input XML paths."""

    # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        # exand the real path to the csv
        values = abspath(realpath(expanduser(expandvars(values))))
        if not os.access(values, os.F_OK, follow_symlinks=True):
            raise argparse.ArgumentError(
                self,
                f"The path '{values}' to test cases does not appear "
                + "to exist. Enter a valid one.",
            )
        xml_paths = generator_parser.read_csv(values)
        # set the value in the parser
        setattr(namespace, self.dest, xml_paths)


class CheckXmlAction(argparse.Action):
    """Helper class to check the test case XML."""

    # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):

        if not values:
            return

        if values.strip() == "":
            return

        if os.path.isdir(values):  # if folder provided
            test_paths = paths.run_fast_scandir(values, ext=".xml")
        else:  # if comma separated file(s)
            test_paths = list()
            values = [s.strip() for s in values.split(",")]
            for path in values:
                full_path = abspath(realpath(expanduser(expandvars(path))))
                if not os.access(full_path, os.F_OK, follow_symlinks=True):
                    raise argparse.ArgumentError(
                        self,
                        f"The path '{full_path}' to the "
                        + "test case does not appear to exist!",
                    )
                test_paths.append(full_path)

                # check the xml for Pinned memory
                with open(full_path, "r", encoding="utf-8") as xmlfh:
                    for line in xmlfh.readlines():
                        if (
                            "MEMORY_BLOCK_ALLOCATOR_TYPE" in line
                            and "PINNEDMEM" in line
                        ):
                            raise argparse.ArgumentError(
                                self,
                                "The Pinned Memory Allocator "
                                + "is not supported with this script.",
                            )

                # set the value in the parser
        setattr(namespace, self.dest, test_paths)


class DefaultTestAction(argparse.Action):
    """
    Helper class to handle default test cases for the IMC tool.
    """

    def parse_test_case_input(self, parser, input_str) -> list:
        # If the input is numeric, treat it as index only for isa filtered tests
        # If the input is a range or comma-separated values, parse it
        if re.match(r"^\d+(-\d+)?(,\s*\d+(-\d+)?)*$", input_str):
            indices = []
            parsed_tests = []
            for part in input_str.split(","):
                # range are only supported when using index based parameters
                if "-" in part:
                    start, end = part.split("-")
                    if start.isdigit() and end.isdigit():
                        indices.extend(range(int(start), int(end) + 1))
                else:
                    # If it's a single number, add it to indices
                    if part.isdigit():
                        indices.append(int(part))
            # validate indices
            for idx in indices:
                if idx < 0 or idx >= len(self.isa_filtered_tests):
                    parser.error(
                        f"Index {idx} is out of range. Valid indices: 0-{len(self.isa_filtered_tests)-1}.",
                    )
            if not indices:
                parser.erro(
                    f"No valid indices provided. Valid indices: 0-{len(self.isa_filtered_tests)-1}.",
                )
            else:
                parsed_tests = [self.isa_filtered_tests[idx] for idx in indices]
                return parsed_tests
        # Otherwise, search for a file matching the test name
        available_tests = []  # Available tests for error message
        parsed_files = []
        for test in input_str.split(","):
            for file in self.default_tests:
                try:
                    # only consider the file_name part of the path
                    file_basename = os.path.basename(file)
                except ValueError:
                    continue
                available_tests.append(file_basename)
                # Allow match with or without .xml extension
                if file_basename == test or file_basename == test + ".xml":
                    parsed_files.append(file)
        if len(parsed_files) == len(input_str.split(",")):
            # If we found all requested parsed files, return them
            return parsed_files
        # If we dont find a match for the parsed parameters, error
        parser.error(
            f"Some or all of the provided test case(s) '{input_str}' were not found. \nOnly the following test(s)"
            + f" were found: {', '.join(os.path.basename(file) for file in parsed_files)}. \nPlease provide valid default test(s) from the available tests:\n"
            + "\t".join(available_tests),  # noqa: E501
        )

    def __init__(self, option_strings, dest, **kwargs):
        systemHandler = LazyLoader.load(
            "scripts.libs.system_handler", "SystemHandler"
        )
        paths = LazyLoader.load("scripts.libs.utils.paths")
        self.instruction_set = (
            systemHandler().os_system.get_highest_cpu_instruction_set()
        )

        # Define potential paths to check
        potential_paths = []
        if systemHandler().os_system.platform_name in ["linux", "svos"]:
            # Debian Package
            potential_paths.append(
                os.path.normcase(
                    "/usr/share/intelligentmemorychecker/customer_tests/"
                )
            )
            potential_paths.append(
                paths.fix_full_path_from_root(
                    os.path.normcase(
                        "/../share/intelligentmemorychecker/customer_tests"
                    )
                )
            )
        potential_paths.append(
            paths.fix_full_path_from_root(os.path.normcase("/customer_tests"))
        )
        potential_paths.append(
            paths.fix_full_path_from_root(
                os.path.normcase(
                    "/ci_cd/resources/specific_functionalities/customer_tests"
                )
            )
        )
        # First find the highest instruction test cases, these will be the ones
        # that we print on the help message.
        self.default_tests = list()
        self.isa_filtered_tests = list()
        for path in potential_paths:
            try:
                isa_test_path = os.path.join(path, self.instruction_set)
                if os.path.isdir(isa_test_path):
                    # Obtain the tests that match the highest instruction
                    self.isa_filtered_tests = paths.run_fast_scandir(
                        isa_test_path, ".xml"
                    )
                    # Obtain all the possible default tests
                    self.all_default_tests = paths.run_fast_scandir(
                        path, ".xml"
                    )
                    if self.isa_filtered_tests and self.all_default_tests:
                        # Use the default tests array to converge the tests,
                        # making sure that the tests from the highest
                        # instruction set are at the beginning of the list
                        self.default_tests.extend(self.isa_filtered_tests)
                        self.default_tests.extend(
                            [
                                test
                                for test in self.all_default_tests
                                if test not in self.isa_filtered_tests
                            ]
                        )
                        break
            except FileNotFoundError:
                continue
        # Help message prints only tests from highest instruction set folder,
        # but the user may provide a command line option for any test found
        # in a specific path
        if "help" in kwargs and self.isa_filtered_tests:
            kwargs[
                "help"
            ] += f"\n\nThe largest instruction set for this system is {self.instruction_set}, some possible test cases are (0-{len(self.isa_filtered_tests)-1}):\n"
            for index, folder in enumerate(self.isa_filtered_tests):
                kwargs["help"] += (
                    " " + str(index) + " - " + os.path.basename(folder) + "\n"
                )
            kwargs["help"] += "\n"
        else:
            kwargs["help"] = (
                "No test cases found in the following default paths:\n"
            )
            for folder in potential_paths:
                kwargs["help"] += f"{folder} \n"

        super().__init__(option_strings, dest, **kwargs)

    # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        if self.default_tests is None:
            parser.error(
                "No test cases found in the default paths. Please provide a valid path or review the paths listed in help."
            )
        test_files = self.parse_test_case_input(parser, values.strip())
        setattr(namespace, self.dest, test_files)


def verify_inclusive_args(args):
    """Verifies that args were sent correctly if it's a inclusive group."""
    if (
        args.csv_path
        and not args.xml_path
        or args.xml_path
        and not args.csv_path
    ):
        raise argparse.ArgumentTypeError(
            "An output path must be provided for generated xml."
        )
    return True


def block_sz_type(value: str):
    """Verifies that the value entered is a number greater than 256."""
    min_block_sz = 256
    try:
        if value.lower().endswith("kb") and len(value) >= 3:
            value = int(value[:-2]) * (2**10)  # convert MB value to Bytes
        elif value.lower().endswith("mb") and len(value) >= 3:
            value = int(value[:-2]) * (2**20)  # convert MB value to Bytes
        elif value.lower().endswith("gb") and len(value) >= 3:
            value = int(value[:-2]) * (2**30)  # convert GB value to Bytes
        else:
            value = int(value)  # default is Bytes
        if value < min_block_sz:
            raise ValueError
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            f"Block size must be a number larger than {min_block_sz} Bytes."
        ) from err
    return value


class CheckXmlPathAction(argparse.Action):
    """
    An argparse function used to check the output path to created xml files
    exists, if not create it."""

    def __call__(self, parser, namespace, values, option_string=None):
        values = abspath(realpath(expanduser(expandvars(values))))
        if not os.access(values, os.F_OK, follow_symlinks=True):
            raise argparse.ArgumentError(
                self,
                f"The path '{values}' to the test case does not appear to exist!",
            )

        # check the xml for Pinned memory
        with open(values, "r", encoding="utf-8") as xmlfh:
            for line in xmlfh.readlines():
                if "memory_block_type" in line and "PINNEDMEM" in line:
                    raise argparse.ArgumentError(
                        self,
                        "The Pinned Memory Allocator is not supported \
                            with this script.",
                    )

        # set the value in the parser
        setattr(namespace, self.dest, values)


def filterString(char_to_filter, long_cmd):
    """
    Checks for char in between arguments to create a list of strings only
    """
    return long_cmd.split(char_to_filter, long_cmd)


ALLOCATOR = "allocator"
BLOCK_SIZE = "block_size"
BLOCKS_AMOUNT = "blocks_amount"
MEM_USAGE = "mem_usage"
TARGET_PATH = "target_path"
PHYSICAL_ADDRESS = "physical_address"
PHYSICAL_ADDRESS_HIGH = "physical_address_high"
PHYSICAL_ADDRESS_LOW = "physical_address_low"
MAPPING_MODE = "mapping"
ENABLE_READ_MAPPING = "enable_read_mapping"
ENABLE_WRITE_MAPPING = "enable_write_mapping"
ENABLE_EXEC_MAPPING = "enable_exec_mapping"
ALLOW_ALIASING = "allow_aliasing"
