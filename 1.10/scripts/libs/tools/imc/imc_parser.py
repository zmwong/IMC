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
This module provides the utilities required for parsing the IMC tool parameters.
"""
import sys
import os
import argparse
from typing import List
import scripts.libs.utils.arg_support as argspt
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.definitions.imc import TOOL_NAME
from scripts.libs.definitions.errors import PROVIDER_NAMES
from scripts.libs.utils.lpu import get_lpu_list
from scripts.libs.utils import stress
from scripts.libs.utils import numa
from scripts.libs.definitions.imc import MEM_USE_DFLT
from scripts.libs.system_handler import SystemHandler
from scripts.libs.definitions.paths import DefaultPaths
from scripts.libs.definitions.imc import BinaryNames
from scripts.libs.utils.paths import fix_full_path_from_root


def compute_default_imc_path() -> str:
    os_name = SystemHandler().os_system.platform_name
    if os_name in ["linux", "svos"]:
        default_compiled = fix_full_path_from_root(
            DefaultPaths.COMPILED_TOOL_BINARY + BinaryNames.REGULAR_BINARY
        )
        default_installed = (
            DefaultPaths.INSTALLED_DPKG + BinaryNames.DEBIAN_PACKAGE_BINARY
        )
        if os.path.exists(default_installed):
            return default_installed
        # Assume binary is in the same directory as the symlink
        if os.path.islink(sys.argv[0]):
            binary_basedir = os.path.dirname(os.path.abspath(sys.argv[0]))
            default_extracted = os.path.join(
                binary_basedir, BinaryNames.DEBIAN_PACKAGE_BINARY
            )
            if os.path.exists(default_extracted):
                return default_extracted
        if os.path.exists(default_compiled):
            return default_compiled
        return None
    if os_name == "windows":
        default_bin = fix_full_path_from_root("/" + BinaryNames.WINDOWS_BINARY)
        return default_bin if os.path.exists(default_bin) else None
    return None


def parse_args_list(argv: List[str]) -> argparse.Namespace:
    """Parses the command line arguments of the IMC tool and returns the parsers namespace

    :param argv: list of command-line arguments
    :return: Parsed argument namespace
    """
    default_imc = compute_default_imc_path()

    parser = argparse.ArgumentParser(
        description="Python Script to call Intelligent Memory Checker",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        dest="xml_path",
        metavar="XMLPATH",
        nargs="?",
        action=argspt.CheckXmlAction,
        help=f"Path(s) to the {TOOL_NAME} test case xml file(s). Multiple "
        + "test cases can be supplied using a comma between file paths or "
        + "by providing a folder path.",
    )

    parser.add_argument(
        "--test_case",
        action=argspt.DefaultTestAction,
        help=f"Specify a predefined {TOOL_NAME} XML test case to run.\n\n"
        + "Test cases may be selected by: \n "
        + "- Index: Use a comma-separated list (e.g., 1,2,3) or range (e.g., 1-5) \n "
        + "- Name: Use the name (with or without the .xml extension) of any test found "
        + "in the 'customer_tests' directory (e.g., <test_case_name> "
        + "or <test_case_name>.xml)",
    )

    parser.add_argument(
        "-e",
        "--executable",
        dest="imc_path",
        metavar="BINPATH",
        default=default_imc,
        help=f"Path to the {TOOL_NAME} binary. Default: %(default)s",
    )
    for i in numa.get_node_count(True):
        parser.add_argument(
            f"--numa{i}",
            dest="numa",
            metavar="NUMBER",
            default={},
            action=argspt.NumaLpuAction,
            help=f"Logical cpu processor number(s) to execute test cases "
            + f"against on numa node {i}. Comma separated. "
            + "Cannot be used in conjunction with -l / --lpu option.",
        )
    parser.add_argument(
        "-l",
        "--lpu",
        dest="lpus",
        metavar="NUMBER",
        default=[],
        action=argspt.NumaLpuAction,
        help="Logical CPU processor number(s) to execute test cases against. "
        + "Comma separated. If none specified ALL logical processors will "
        + "be used. Cannot be used in conjunction with --numa option.",
    )

    parser.add_argument(
        "-p",
        "--provider",
        dest="provider",
        metavar="PROVIDER",
        default="none",
        choices=PROVIDER_NAMES.keys(),
        help=f"Specify the provider used to collect errors. Valid options: "
        + f'{", ".join(PROVIDER_NAMES)}. Default is %(default)s and will '
        + "not use an error provider.",
    )

    parser.add_argument(
        "-m",
        "--memory_usage",
        dest="mem_use",
        metavar="PERCENTAGE",
        default=f"{MEM_USE_DFLT}%",
        type=argspt.mem_value_type,
        help=f"Specifies a percentage of available memory used by all "
        + f"instances of {TOOL_NAME}. If not specified then "
        + f"{MEM_USE_DFLT}%% of available memory will be used.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        dest="timeout",
        metavar="MINUTES",
        default="0",
        type=argspt.timeout_type,
        help=f"Specifies the maximum time in minutes each instance of "
        + f"{TOOL_NAME} can execute before it is automatically terminated. "
        + "This does not prevent early termination before the specified "
        + "time. Default is %(default)s for no timeout.",
    )
    parser.add_argument(
        "--blocksize",
        dest="blk_size",
        metavar="BYTES",
        default=None,
        type=argspt.block_sz_type,
        help=f"{TOOL_NAME} test case block size override. When set the value "
        + "provided will override the automatic block size calculation.",
    )
    parser.add_argument(
        "--time_to_execute",
        dest="time_to_execute",
        metavar="SECONDS",
        default=None,
        type=argspt.time_type,
        help=f"{TOOL_NAME} test case execution time override. When set the value "
        + "provided will override the execution time set on the test case file.",
    )

    parser.add_argument(
        "--pcm_delay",
        dest="pcm_delay",
        metavar="PCM_DELAY",
        default="1",
        type=str,
        help="Specifies the PCM delay value to use. Default: %(default)s.",
    )

    parser.add_argument(
        "--pcm",
        dest="pcm",
        default=False,
        action="store_true",
        help="Enables pcm-memory plugin. Default: %(default)s.",
    )

    parser.add_argument(
        "--pcm_path",
        dest="pcm_path",
        metavar="PCM_PATH",
        default=(
            "/usr/lib/python3/dist-packages/intelligentmemorychecker/scripts/libs/plugins/pcm/pcm-memory"
        ),
        type=str,
        help="Specifies the PCM path to use. Default from debian package: %(default)s.",
    )

    if SystemHandler().os_system.platform_name == "svos":
        parser.add_argument(
            "--target",
            dest="target",
            metavar="TARGETPATH",
            default=None,
            type=str,
            help=f"It specifies the memory target path.",
        )
    parser.add_argument(
        "--stop-on-error",
        dest="stop_on_error",
        action="store_true",
        help="Stops all running instances on first error reported by any "
        + "Intelligent Memory Checker instance. Default: %(default)s.",
    )
    parser.add_argument(
        "--priority",
        dest="priority",
        default="50",
        metavar="NUMBER",
        type=argspt.priority_type,
        help="Sets each instance of Intelligent Memory Checker to the "
        + "specified priority: 1 [least] to 100 [most]. "
        + "Default: %(default)s.",
    )
    parser.add_argument(
        "--stress",
        dest="stress",
        default=None,
        metavar="TYPE",
        action=argspt.StressAction,
        choices=stress.SUPPORTED_STRESS,
        help=f"Uses a pre-defined test case to stress test from: "
        + f'{", ".join(stress.SUPPORTED_STRESS)}. If an XML test case is '
        + "provided it will override the pre-defined test case.",
    )
    parser.add_argument(
        "--execution",
        dest="executionType",
        default="queue",
        choices=["queue", "batch"],
        help="Specify the thread execution type: queue or batch. "
        + "Queue: Each thread takes a test case from the queue and executes an IMC subprocess until "
        + "the queue is empty. Batch: The number of lpus is used to split test cases "
        + "into batches, where each thread receives a test case from the batch. "
        + "Default is %(default)s.",
    )

    parser.add_argument(
        "--stress_variable",
        dest="stress_variable",
        default=False,
        action="store_true",
        help="Enable variable stress mode (sine wave-modulated threads) instead of the default runnable.",
    )

    parser.add_argument(
        "--stress_period",
        dest="stress_period",
        default=60.0,
        type=float,
        metavar="SECONDS",
        help="Period of the sine wave for stress-variable mode type in seconds. "
        + "Determines how long one complete stress cycle takes. Default is %(default)s.",
    )
    parser.add_argument(
        "--stress_control_interval",
        dest="stress_control_interval",
        default=0.25,
        type=float,
        metavar="SECONDS",
        help="Control interval for stress-variable mode type in seconds. "
        + "Determines how frequently the stress level is adjusted. Smaller values provide "
        + "more responsive control but increase overhead. Default is %(default)s.",
    )
    parser.add_argument(
        "-v",
        dest="verbosity",
        default=4,
        action=argspt.VerboseAction,
        help="Sets available verbosity level. -v off turns off all output to "
        + "the screen. Default is -vvvv.",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=str(1.8),
        help="Display the current IMC version",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as parse_exit:
        if parse_exit.code == 0:
            sys.exit(parse_exit.code)
        sys.exit(int(ExitCode.RUNNER_TOOL_FAILED))

    if args.xml_path is None and args.test_case is None:
        parser.error("No XMLPATH or default option was provided.")

    if args.xml_path and args.test_case:
        parser.error(
            "Both XMLPATH and default options were provided. Please specify one or the other."
        )

    if args.test_case:
        args.xml_path = args.test_case

    args.provider = PROVIDER_NAMES.get(args.provider)
    # check if lpus or numa is used, if neither were used default to lpus:
    if not args.lpus and not (hasattr(args, "numa") and bool(args.numa)):
        args.lpus = get_lpu_list()
    # if no bin path is give, use default
    if not args.imc_path:
        args.imc_path = default_imc
    return args
