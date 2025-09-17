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
This module is a Python wrapper intended to call the test generator module to
set a test case file (or multiple tests files) to be used on Intelligent Memory
Checker. The generation of the tests can be done via command line arguments,
command line interface through menus or through a CSV file.
If app command is specified it orchestrates execution of Intelligent Memory
Checker through the runner.
runner.
"""
import sys
import os
import argparse
import subprocess
import signal
import csv
from typing import List
from datetime import datetime

import libs.utils.arg_support as argspt
import libs.utils.paths as paths
import libs.utils.arg_support as argspt
from scripts.libs.utils import numa
from scripts.libs.definitions.imc import BinaryNames, MEM_USE_DFLT
from scripts.libs.test_generator import generator_main
from scripts.libs.utils.logging import Level
from scripts.libs.definitions.paths import DefaultPaths
from scripts.libs.utils.environment import EnvironmentInfo
from scripts.libs.utils.arg_support import (
    ALLOCATOR,
    ALLOW_ALIASING,
    PHYSICAL_ADDRESS,
)
from scripts.libs.utils.arg_support import (
    PHYSICAL_ADDRESS_HIGH,
    PHYSICAL_ADDRESS_LOW,
)
from scripts.libs.utils.arg_support import (
    TARGET_PATH,
    BLOCK_SIZE,
    BLOCKS_AMOUNT,
)
from scripts.libs.utils.arg_support import (
    ENABLE_EXEC_MAPPING,
    ENABLE_WRITE_MAPPING,
)
from scripts.libs.utils.arg_support import (
    MEM_USAGE,
    MAPPING_MODE,
    ENABLE_READ_MAPPING,
)
from scripts.libs.test_generator import generator_parser
from scripts.libs.definitions.imc import ParameterIdentifier
from scripts.libs.definitions.imc import IMCMemory, TOOL_NAME
from scripts.libs.definitions.exit_codes import ExitCode
from scripts.libs.utils.arg_support import VerboseAction
from scripts.libs.test_generator.menu import generate_tests_via_menu
from scripts.libs.utils.paths import fix_full_path_from_root
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)

__author__ = "Sofia Salazar"
__credits__ = ["Sofia Salazar, Alan Lomeli"]
__copyright__ = "Copyright 2024, Intel Corporation All Rights Reserved."
__license__ = "Confidential"
__version__ = "0.2"
__status__ = "Development"

REQ_VER = (3, 6)

files_with_errors = []

if not sys.version_info[0:2] >= REQ_VER:
    raise RuntimeError(
        f"This module requires Python {'.'.join([str(v) for v in REQ_VER])} "
        + "or newer."
    )

# Global variables


def ctrl_handler(signum, frame):
    """Runs when the user presses Ctrl-C"""
    LogManager().log(
        "IMC",
        LogManagerThread.Level.WARNING,
        "Ctrl+C was detected. Exiting program...",
    )
    exit(1)


def pretty_exit(exit_code: int):
    """
    Shows info in logs according to exit code.

    :param exit_code: Exit Code.
    """
    exit_str = f"Process finished. EXIT_CODE: {int(exit_code)}."
    if exit_code == 0:
        LogManager().log(
            "IMC",
            LogManagerThread.Level.INFO,
            exit_str + " No errors during execution.",
        )
    else:
        LogManager().log(
            "IMC",
            LogManagerThread.Level.CRITICAL,
            exit_str + " Error during execution.",
        )
    sys.exit(int(exit_code))


def _parse_args(argv: List[str]):
    """
    Parses the command line arguments and returns the parsers namespace
    :param argv: list of command-line arguments
    :return: Parsed argument namespace
    """
    environment_info = EnvironmentInfo()
    parser = argparse.ArgumentParser(
        description="Python Script to run IMC test cases"
    )
    parser.add_argument(
        "--runner_logs",
        action="store_true",
        help="check if csv log files will be generated after Runner execution.",
        required=False,
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="run command line menu for test generation",
        required=False,
    )
    parser.add_argument(
        "--csv_path",
        dest="csv_path",
        metavar="<csv_path>",
        action=argspt.CheckCsvAction,
        default=None,
        help="path to the csv file to generate test cases",
    )
    parser.add_argument(
        "--tests_path",
        dest="tests_path",
        metavar="<tests_path>",
        default=None,
        help="path to the existing xml test cases",
    )
    parser.add_argument(
        "--app",
        action="store_true",
        help="launch IMC app with generated tests.",
        required=False,
    )
    parser.add_argument(
        "--output_path",
        metavar="<path>",
        default=DefaultPaths.GENERATED_TESTS,
        help="output path where tests will be generated",
    )

    """ Parameteres to call the imc_runner. """
    runner = parser.add_argument_group("runner parameters")
    runner.add_argument(
        "-e",
        "--executable",
        dest="imc_path",
        metavar="BINPATH",
        help=f"path to the {TOOL_NAME} binary.",
    )
    for i in numa.get_node_count(True):
        runner.add_argument(
            f"--numa{i}",
            dest="numa",
            metavar="NUMBER",
            default={},
            action=argspt.NumaLpuAction,
            help=f"logical cpu processor number(s) to execute test cases "
            + f"against on numa node {i}. Comma separated."
            + f" Cannot be used in conjunction with -l / --lpu option.",
        )
    runner.add_argument(
        "-l",
        "--lpu",
        dest="lpus",
        default=[],
        action=argspt.NumaLpuAction,
        help="logical CPU processor number(s) to execute test cases against."
        + "Comma separated.  If none specified ALL logical processors will "
        + "be used.  Cannot be used in conjunction with --numa option.",
    )
    runner.add_argument(
        "-m",
        "--memory_usage",
        dest="mem_use",
        metavar="PERCENTAGE",
        default=f"{MEM_USE_DFLT}%",
        type=argspt.mem_value_type,
        help="specifies a percentage of available memory used by all "
        + f"instances of {TOOL_NAME}. If not specified then "
        + f"{MEM_USE_DFLT}%% of available memory will be used.",
    )
    runner.add_argument(
        "-t",
        "--timeout",
        dest="timeout",
        metavar="MINUTES",
        default="0",
        type=argspt.timeout_type,
        help=f"maximum time in minutes each instance of {TOOL_NAME} can "
        + "execute before it is automatically terminated. This does not "
        + "prevent early termination before the specified time. Default: 0.",
    )
    runner.add_argument(
        "--blocksize",
        dest="blk_size",
        metavar="BYTES",
        default=None,
        type=argspt.block_sz_type,
        help=f"{TOOL_NAME} test case block size override. When set the value"
        + "provided will override the automatic block size calculation.",
    )
    if environment_info.OS == "SVOS":
        runner.add_argument(
            "--target",
            dest="target",
            metavar="TARGETPATH",
            default=None,
            type=str,
            help=f"It specifies the full memory target path.",
        )
    runner.add_argument(
        "--stop-on-error",
        dest="stop_on_error",
        action="store_true",
        help="stops all running instances on first error reported by any "
        + "Intelligent Memory Checker instance.",
    )
    runner.add_argument(
        "--priority",
        dest="priority",
        default="50",
        metavar="NUMBER",
        help="sets each instance of Intelligent Memory Checker to the "
        + "specified priority: 1 [least] to 100 [most].  Default is 50.",
    )

    """ Paramateres to call the imc_compile script. """
    compilation = parser.add_argument_group("compilation parameters")
    compilation.add_argument(
        "--info_logs",
        dest="info_logs",
        action="store_true",
        help="enable info logs for tool compilance",
    )
    compilation.add_argument(
        "--debug_logs",
        dest="debug_logs",
        action="store_true",
        help="enable debug logs for tool compilance",
    )
    parser.add_argument(
        "--environment",
        type=str,
        help="Environment target for tool compilation LINUX/SVOS.",
    )
    compilation.add_argument(
        "--disable_avx512",
        action="store_true",
        help="Disable support for AVX512 on compilation.",
    )
    compilation.add_argument(
        "-u",
        "--unitTest",
        action="store_true",
        help="Enable a unit test for the tool (default: %(default)s).",
    )
    compilation.add_argument(
        "--library",
        action="store_true",
        help="Enable shared library option. Note: This option does not work "
        + "for SHARED_LIBRARY environment (default: %(default)s).",
    )
    compilation.add_argument(
        "--disable_tool",
        action="store_true",
        help="Enable tool generation only on LINUX and SVOS "
        + "(default: %(default)s).",
    )

    compilation.add_argument(
        "--disable_fast_logs",
        action="store_true",
        help="Enable fast logs (default: %(default)s).",
    )

    compilation.add_argument(
        "-f",
        "--format",
        type=str,
        default="HEXADECIMAL",
        help="Numeric base format to display data in logs"
        + "(default: %(default)s).",
    )
    compilation.add_argument(
        "--enable_compilation_logs",
        action="store_true",
        help="Disable output from compiling script",
    )

    """ Group parameters to make custom test through command line. """
    test_generator = parser.add_argument_group("custom test generator")

    """ All valid parameters to modify test case through command line."""
    # Global control
    test_generator.add_argument(
        f"--{ParameterIdentifier.GLOBAL_ITERATIONS.value}",
        metavar="NUMBER",
        default=1,
        help=" amount of iterations the tool will run "
        + "if time is selected skip this parameter",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.GLOBAL_TIME_TO_EXECUTE.value}",
        metavar="<TIME_UNIT>",
        help="control execution time, if iterations is selected "
        + "skip this parameter",
    )
    # todo action to verify global iterations is not defined
    test_generator.add_argument(
        f"--{ParameterIdentifier.FLOW_TYPE.value}",
        metavar="<flow type>",
        help="select flow type to run",
    )
    test_generator.add_argument(
        f"--{ALLOCATOR}",
        metavar="MODE",
        default="MALLOC",
        help="memory allocator type for memory blocks",
    )
    test_generator.add_argument(
        f"--{BLOCK_SIZE}",
        metavar="NUMBER",
        default="512",
        help=" memory block size in bytes",
    )
    test_generator.add_argument(
        f"--{BLOCKS_AMOUNT}", metavar="NUMBER", help="amount of memory blocks"
    )
    test_generator.add_argument(
        f"--{MEM_USAGE}",
        metavar="NUMBER",
        help="total memory usage for memory group creation",
    )
    test_generator.add_argument(
        f"--{MAPPING_MODE}",
        metavar="MODE",
        default="SHARED",
        help="SHARED | PRIVATE",
    )
    test_generator.add_argument(
        f"--{TARGET_PATH}",
        metavar="MODE",
        help="memory group target path selection",
    )
    test_generator.add_argument(
        f"--{PHYSICAL_ADDRESS}",
        metavar="MODE",
        help="valid memory address on hex format",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.ITERATIONS.value}",
        metavar="NUMBER",
        help="iterations on inner executions",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.ADDRESS_ALGORITHM_TYPE.value}",
        metavar="<algorithm type>",
        help="supported address algorithm by the flow",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.DATA_ALGORITHM_TYPE.value}",
        metavar="<algorithm type>",
        help="supported data algorithm by the flow",
    )
    test_generator.add_argument(
        f"--{PHYSICAL_ADDRESS_HIGH}",
        metavar="MODE",
        help="physical address high flag",
    )
    test_generator.add_argument(
        f"--{PHYSICAL_ADDRESS_LOW}",
        metavar="MODE",
        help="physical address low flag",
    )
    test_generator.add_argument(
        f"--{ENABLE_READ_MAPPING}", metavar="MODE", help="read mapping flag"
    )
    test_generator.add_argument(
        f"--{ENABLE_WRITE_MAPPING}", metavar="MODE", help="write mapping flag"
    )
    test_generator.add_argument(
        f"--{ENABLE_EXEC_MAPPING}",
        metavar="MODE",
        help="execution mapping flag",
    )
    test_generator.add_argument(
        f"--{ALLOW_ALIASING}", metavar="BOOL", help="aliasing flag"
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.OPCODE.value}",
        metavar="<opcode>",
        default="LEGACY",
        help="{}".format(
            ", ".join(generator_parser.get_supported_opcode_names())
        ),
    )
    """ Flow  configuration commands """
    test_generator.add_argument(
        f"--{ParameterIdentifier.ALIGNMENT.value}",
        metavar="NUMBER",
        help=" alignment on writing/reading",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.DATA_BURSTS.value}",
        metavar="NUMBER",
        help="number of flows for burster flow",
    )
    test_generator.add_argument(
        "--same_address",
        dest=ParameterIdentifier.SAME_ADDRESS.value,
        metavar="BOOL",
        help="same address flag for burster flow",
    )
    test_generator.add_argument(
        "--restart",
        dest=ParameterIdentifier.RESTART_ALGORITHM_AT_ITERATION.value,
        metavar="BOOL",
        help="restart algorithm flag",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.MARCH_ELEMENT.value}",
        metavar="<list>",
        default="up,wI,rI",
        help="list/lists separated by comma for march algorithm",
    )

    """ Algorithm specific parameteres"""
    test_generator.add_argument(
        f"--{ParameterIdentifier.NUMBER_BYTES_TO_REPEAT.value}",
        metavar="NUMBER",
        help="number bytes to repeat",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.PATTERN_LIST.value}",
        metavar="<list>",
        help="pattern list for pattern list algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.DATA_INCREMENTOR}",
        metavar="NUMBER",
        help="decrementor for data algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.ADDRESS_DECREMENTOR}",
        metavar="NUMBER",
        help="decrementor for address algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.ADDRESS_SEED}",
        metavar="SEED",
        help="seed for address algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.DATA_SEED}",
        metavar="SEED",
        help="seed for data algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.CHANGE_PIVOT}",
        metavar="BOOL",
        help="change pivot flag for pivot algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.PIVOT_INITIAL_POSITION}",
        metavar="NUMBER",
        help="pivot initial position for pivot algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.SET_STRIDE}",
        metavar="NUMBER",
        help="used on set associative algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.WAY_STRIDE}",
        metavar="NUMBER",
        help="used on set associative algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.BLOCKS_PER_SET}",
        metavar="NUMBER",
        help="number of blocks used on set associative algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.MAX_SETS_TO_EVICT}",
        metavar="NUMBER",
        help="used on set associative algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.WEDGE_SIZE}",
        metavar="NUMBER",
        help="size used on wedge algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.CHANGE_WEDGE}",
        metavar="BOOL",
        help="used on wedge algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.NUMBER_CACHE_LINES}",
        metavar="NUMBER",
        help="used on xtalk algorithm",
    )
    test_generator.add_argument(
        f"--{ParameterIdentifier.SECONDARY}",
        metavar="BOOL",
        help="used on xtalk algorithm ",
    )

    parser.add_argument(
        "-V", "--version", action="version", version=str(__version__)
    )
    parser.add_argument(
        "-v",
        dest="verbosity",
        default=4,
        action=VerboseAction,
        help="Sets available verbosity level. -v off turns off all output to "
        + "the screen.  Default is -vvvv.",
    )

    return parser.parse_args(argv)


def check_memory_options(dictionary):
    """Prepares the memory parameters to be written to the test when using the
    CLI, since other parameters can be created directly, but memory parameters
    require additional validation."""
    if dictionary[BLOCKS_AMOUNT] not in [None, ""]:  # If using memory blocks
        dictionary[ParameterIdentifier.MEMORY_BLOCK_AMOUNT.value] = dictionary[
            BLOCKS_AMOUNT
        ]
        dictionary[ParameterIdentifier.MEMORY_SIZE_IN_BYTES.value] = dictionary[
            BLOCK_SIZE
        ]
        dictionary[ParameterIdentifier.MEMORY_BLOCK_ALLOCATOR_TYPE.value] = (
            dictionary[ALLOCATOR]
        )

        # If using SVOS allocator
        if dictionary[ALLOCATOR] == IMCMemory.SVOS.NAME:
            dictionary[ParameterIdentifier.MEMORY_BLOCK_TARGET_PATH] = (
                dictionary[TARGET_PATH]
            )
            dictionary[ParameterIdentifier.MEMORY_BLOCK_MAPPING_MODE] = (
                dictionary[MAPPING_MODE]
            )
            dictionary[
                ParameterIdentifier.MEMORY_BLOCK_PHYSICAL_ADDRESS_HIGH
            ] = dictionary[PHYSICAL_ADDRESS_HIGH]
            dictionary[
                ParameterIdentifier.MEMORY_BLOCK_PHYSICAL_ADDRESS_LOW
            ] = dictionary[PHYSICAL_ADDRESS_LOW]
            dictionary[ParameterIdentifier.MEMORY_BLOCK_PHYSICAL_ADDRESS] = (
                dictionary[PHYSICAL_ADDRESS]
            )
            dictionary[ParameterIdentifier.MEMORY_BLOCK_ENABLE_READ_MAPPING] = (
                dictionary[ENABLE_READ_MAPPING]
            )
            dictionary[
                ParameterIdentifier.MEMORY_BLOCK_ENABLE_WRITE_MAPPING
            ] = dictionary[ENABLE_WRITE_MAPPING]
            dictionary[ParameterIdentifier.MEMORY_BLOCK_ENABLE_EXEC_MAPPING] = (
                dictionary[ENABLE_EXEC_MAPPING]
            )
            dictionary[ParameterIdentifier.MEMORY_BLOCK_ALLOW_ALIASING] = (
                dictionary[ALLOW_ALIASING]
            )

    elif dictionary[MEM_USAGE] not in [None, ""]:  # If using memory groups
        dictionary[ParameterIdentifier.MEMORY_GROUP_OVERALL.value] = dictionary[
            MEM_USAGE
        ]
        dictionary[ParameterIdentifier.MEMORY_GROUP_SIZE_IN_BYTES.value] = (
            dictionary[BLOCK_SIZE]
        )
        dictionary[ParameterIdentifier.MEMORY_GROUP_BLOCK_TYPE.value] = (
            dictionary[ALLOCATOR]
        )

        # If using SVOS allocator
        if dictionary[ALLOCATOR] == IMCMemory.SVOS.NAME:
            dictionary[ParameterIdentifier.MEMORY_GROUP_TARGET_PATH] = (
                dictionary[TARGET_PATH]
            )
            dictionary[ParameterIdentifier.MEMORY_GROUP_MAPPING_MODE] = (
                dictionary[MAPPING_MODE]
            )
            dictionary[
                ParameterIdentifier.MEMORY_GROUP_PHYSICAL_ADDRESS_HIGH
            ] = dictionary[PHYSICAL_ADDRESS_HIGH]
            dictionary[
                ParameterIdentifier.MEMORY_GROUP_PHYSICAL_ADDRESS_LOW
            ] = dictionary[PHYSICAL_ADDRESS_LOW]
            dictionary[ParameterIdentifier.MEMORY_GROUP_PHYSICAL_ADDRESS] = (
                dictionary[PHYSICAL_ADDRESS]
            )
            dictionary[ParameterIdentifier.MEMORY_GROUP_ENABLE_READ_MAPPING] = (
                dictionary[ENABLE_READ_MAPPING]
            )
            dictionary[
                ParameterIdentifier.MEMORY_GROUP_ENABLE_WRITE_MAPPING
            ] = dictionary[ENABLE_WRITE_MAPPING]
            dictionary[ParameterIdentifier.MEMORY_GROUP_ENABLE_EXEC_MAPPING] = (
                dictionary[ENABLE_EXEC_MAPPING]
            )

    return dictionary


def check_runner_options(parsed_args, environment):
    """Verify the parsed_args runner options."""
    runner_args = []
    #    if parsed_args.numa:
    #        runner_args += ['--numa', str(parsed_args.numa)]
    if parsed_args.lpus:
        runner_args += ["--lpu", str(parsed_args.lpus)[1:-1]]
    if parsed_args.mem_use:
        runner_args += ["--m", str(parsed_args.mem_use)]
    if parsed_args.timeout:
        runner_args += ["--t", str(parsed_args.timeout)]
    if parsed_args.blk_size:
        runner_args += ["--blocksize", str(parsed_args.blk_size)]
    if environment == "SVOS":
        if parsed_args.target:
            runner_args += ["--target", str(parsed_args.target)]
    if parsed_args.stop_on_error:
        runner_args += ["--stop-on-error"]
    if parsed_args.priority:
        runner_args += ["--priority", str(parsed_args.priority)]
    return runner_args


def search_for_status_code(actual_status_code):
    """Search for a status code in a list.

    :return: (status_code_number, status_code_name, status_code_description)
    """
    status_code_list = []
    for name, member in ExitCode.__members__.items():
        status_code_list.append(
            [str(name), int(member.value), str(member.description)]
        )

    status_code_number = ""
    status_code_name = ""
    status_code_description = ""
    for name, number, description in status_code_list:
        if (
            actual_status_code == number
            or actual_status_code == name
            or actual_status_code == description
        ):
            status_code_number = number
            status_code_name = name
            status_code_description = description
            break

    return (status_code_name, status_code_number, status_code_description)


def _call_runner(files, binary, runner_cmd, imc_runner_path):
    """Execute test cases using runner.

    :return: Files execution status codes
    """
    execution_status = []
    for file in files:
        row = {"Runner execution": file}
        LogManager().log("IMC", LogManagerThread.Level.INFO, f"Testing: {file}")
        row["Runner execution"] = file
        # Executing Runner
        cmd_script = [
            "python",
            imc_runner_path,
            "--executable",
            binary,
            file,
        ]
        cmd_script += runner_cmd
        process = subprocess.run(cmd_script)
        row["Runner exit code"] = process.returncode
        row["Runner status code"] = search_for_status_code(process.returncode)
        if process.returncode != 0:
            global files_with_errors
            files_with_errors.append(file)
        execution_status.append(row)
    return execution_status


def _launch_app(tests_dir, binary_path, runner_args, imc_runner_path):
    """
    Call runner with generated files. Check default path to generated files if
    not specified.
    return: exit code
    """
    execution_logs = []
    if not os.access(tests_dir, os.F_OK, follow_symlinks=True):
        raise ValueError(f"The path '{tests_dir}' does not appear to exist!")
    # Find all subidrs and files
    files = paths.run_fast_scandir(tests_dir, ext=".xml")
    if (len(files)) > 0:
        # Executing runner
        execution_logs += _call_runner(
            files, binary_path, runner_args, imc_runner_path
        )
    else:
        LogManager().log(
            "IMC",
            LogManagerThread.Level.WARNING,
            f"No files were found at {tests_dir}",
        )
    return execution_logs


def processing_output(stdout, stderr):
    """Processing test output.

    :return: (String, String)
    """
    stdout = str(stdout)
    stderr = str(stderr)
    stdout = stdout.replace("\\n", "\n").replace("\\t", "\t")
    stderr = stderr.replace("\\n", "\n").replace("\\t", "\t")

    return (stdout, stderr)


def _compile(environment_info: EnvironmentInfo, parsed_args):
    """Compile IMC app, using compileIMC script. Take environment or parsed args
    flags to call the compilation."""
    cmd_script = [
        "python",
        "compileIMC.py",
        "-c",  # Flag to compile using arguments
        "--tool",
        "--fastLogs",
    ]
    cmd_script.append("--environment")
    if parsed_args.environment:
        cmd_script.append(parsed_args.environment)
    else:
        cmd_script.append(environment_info.OS)
    if parsed_args.info_logs:
        cmd_script.append("--infoLogs")
    if parsed_args.debug_logs:
        cmd_script.append("--debugLogs")
    if parsed_args.disable_avx512 or environment_info.avx512_support is False:
        cmd_script.append("--disable_avx512")
    if parsed_args.unitTest:
        cmd_script.append("--unitTest")
    if parsed_args.library:
        cmd_script.append("--library")
    if parsed_args.disable_tool:
        cmd_script.remove("--tool")
    if parsed_args.disable_fast_logs:
        cmd_script.remove("--fastLogs")
    if parsed_args.format:
        cmd_script.append("--format")
        cmd_script.append(parsed_args.format)
    process = subprocess.Popen(
        cmd_script, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    (stdout, stderr) = process.communicate()
    (stdout, stderr) = processing_output(stdout, stderr)
    status_code = process.wait()
    if parsed_args.enable_compilation_logs:
        LogManager().log("IMC", LogManagerThread.Level.INFO, stdout)
        LogManager().log("IMC", LogManagerThread.Level.INFO, stderr)
    if status_code != 0:
        LogManager().log(
            "IMC", LogManagerThread.Level.ERROR, "Failed at compiling tool."
        )
    else:
        LogManager().log(
            "IMC", LogManagerThread.Level.INFO, "Compilation finished"
        )
        # Update environment info
        # After compiling update binary path (it was None)
        bin_path = fix_full_path_from_root(
            DefaultPaths.COMPILED_TOOL_BINARY + BinaryNames.REGULAR_BINARY
        )
        bin_path = paths.verify_binary_exists(bin_path)
        environment_info._imc_path = bin_path
    return status_code, bin_path


def generate_log_file_name(logs_path, log_type, extension=".csv"):
    """Generate the specific name for the log files.

    :return: String
    """
    now = datetime.now()
    log_file_name = (logs_path + "{}_{}" + extension).format(
        log_type, now.strftime("%d_%m_%Y_%H-%M-%S")
    )

    return log_file_name


def write_csv(log_file_name, lines, write_headers):
    """Write in the final csv the results.

    :return: None
    """

    LOG_HEADERS = ["Runner execution", "Runner status code", "Runner exit code"]

    with open(log_file_name, mode="w") as log_file:
        logger_writer = csv.DictWriter(
            log_file,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            fieldnames=LOG_HEADERS,
        )

        if write_headers:
            logger_writer.writeheader()

        for item in lines:
            logger_writer.writerow(item)


def write_log(log_file_name, lines):
    """Write affected files paths on log.

    :return: None
    """
    with open(log_file_name, mode="w") as log_file:
        if log_file_name.endswith(".txt"):
            msg = "XML files with errors".center(60, "*")
            log_file.write(msg + "\n\n")
            log_file.write("\n".join(lines))
            log_file.write("\n\nYou can check execution on csv file.")


def main():
    """
    Main entry point for starting the generation and launching of tool.
    :param argv: List of arguments that will be parsed
    :return: exit code
    """
    signal.signal(signal.SIGINT, ctrl_handler)
    exit_code = ExitCode.OK
    status_code = ExitCode.OK
    parsed_args = _parse_args(sys.argv[1:])
    output_path = ""
    test_dictionary = None
    generated_tests = False

    # Get tests, by generating or grabbing a test folder
    if parsed_args.csv_path:
        test_dictionary = parsed_args.csv_path

    elif parsed_args.menu:
        test_dictionary = generate_tests_via_menu()

    elif parsed_args.flow_type:
        dict = vars(parsed_args).copy()
        test_dictionary = check_memory_options(dict)

    if test_dictionary:  # Generate test if test_dictionary was set
        output_folder = "generated_tests_" + str(
            datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        )
        output_path = os.path.join(parsed_args.output_path, output_folder)
        status_code = generator_main.generate_tests(
            test_dictionary, write_path=output_path
        )
        LogManager().log(
            "IMC",
            LogManagerThread.Level.INFO,
            "Tests were generated at " + output_path,
        )
        generated_tests = True

    if parsed_args.app:
        execution_status = []
        LogManager().log(
            "IMC",
            LogManagerThread.Level.INFO,
            "Preparing to run application.",
        )
        environment_info = EnvironmentInfo()
        environment_bin = environment_info.imc_path
        argument_bin = parsed_args.imc_path
        runner_path = environment_info.imc_runner_path

        if argument_bin:
            binary_path = paths.verify_binary_exists(argument_bin)
        elif environment_bin:
            binary_path = paths.verify_binary_exists(environment_bin)
        else:
            binary_path = None

        if not binary_path:
            LogManager().log(
                "IMC",
                LogManagerThread.Level.WARNING,
                "Compiling with available options. Please wait...",
            )
            (compile_status, binary_path) = _compile(
                environment_info, parsed_args
            )
            if compile_status != 0:
                pretty_exit(1)

        if not runner_path:
            LogManager().log(
                "IMC",
                LogManagerThread.Level.ERROR,
                "Could not find IMC Runner Python Script. "
                + "Please validate the location of the script.",
            )
            pretty_exit(1)

        runner_args = check_runner_options(parsed_args, environment_info.OS)
        # At this point there is a valid binary to run
        if generated_tests is True:
            if os.path.exists(parsed_args.output_path):
                LogManager().log(
                    "IMC",
                    LogManagerThread.Level.INFO,
                    f"Launching app with files generated at {output_path}.",
                )
                execution_status += _launch_app(
                    output_path, binary_path, runner_args, runner_path
                )
            else:
                LogManager().log(
                    "IMC",
                    LogManagerThread.Level.INFO,
                    "No tests were generated. Finishing Launcher execution.",
                )
        elif parsed_args.tests_path is None:
            if os.path.exists(DefaultPaths.GENERATED_TESTS):
                LogManager().log(
                    "IMC",
                    LogManagerThread.Level.INFO,
                    f"Launching app with generated files at default path: "
                    + f"{DefaultPaths.GENERATED_TESTS}",
                )
                execution_status += _launch_app(
                    DefaultPaths.GENERATED_TESTS,
                    binary_path,
                    runner_args,
                    runner_path,
                )
        elif parsed_args.tests_path:
            if os.path.exists(parsed_args.tests_path):
                LogManager().log(
                    "IMC",
                    LogManagerThread.Level.INFO,
                    f"Launching app with existing files at "
                    + f"{parsed_args.tests_path}",
                )
                execution_status += _launch_app(
                    parsed_args.tests_path,
                    binary_path,
                    runner_args,
                    runner_path,
                )

        if parsed_args.runner_logs:
            # Save logs into csv file
            logs_path = "launcher_logs/"
            paths.check_make_dir(logs_path)
            log_file = generate_log_file_name(
                logs_path, "launcher_execution", ".csv"
            )
            error_files = generate_log_file_name(
                logs_path, "launcher_error_files", ".txt"
            )
            # Write execution log
            write_csv(log_file, execution_status, True)
            # Write error files
            write_log(error_files, files_with_errors)

        # Get status codes
        for execution in execution_status:
            if execution["Runner exit code"] != 0:
                exit_code = 1
                break

    if status_code != ExitCode.OK:
        exit_code = 1
    pretty_exit(exit_code)


if __name__ == "__main__":
    main()
