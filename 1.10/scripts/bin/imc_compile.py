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
This module is a Python wrapper to compile the Intelligent Memory Checker tool.
"""
__author__ = "Salazar, Sofia"
__copyright__ = "Copyright 2024, Intel Corporation All Rights Reserved."
__license__ = "Confidential"
__version__ = "0.1"
__status__ = "Development"
import os
import sys
import subprocess
import argparse
import json
from itertools import cycle
from datetime import datetime
from typing import List
from enum import Enum

from scripts.libs.definitions.paths import DefaultPaths
from scripts.libs.definitions.imc import REQ_VER, TOOL_NAME, TargetEnvironment
from scripts.libs.definitions.imc import BinaryNames
from scripts.libs.definitions.headers import INTEL_LOGO
from scripts.libs.utils.arg_support import VerboseAction
from scripts.libs.utils.paths import fix_full_path
from scripts.libs.definitions.exit_codes import ExitCode

if not sys.version_info[0:2] >= REQ_VER:
    raise RuntimeError(
        f"This module requires Python {'.'.join([str(v) for v in REQ_VER])} \
        or newer."
    )

# Global definitions
environments = cycle(TargetEnvironment)
data_display = cycle(["BINARY", "DECIMAL", "HEXADECIMAL"])
off_options = cycle(["ON", "OFF"])
debug_logs = cycle(["ON", "OFF"])
info_logs = cycle(["ON", "OFF"])
unit_test = cycle(["ON", "OFF"])
library = cycle(["ON", "OFF"])
tool = cycle(["OFF", "ON"])
fast_logs = cycle(["OFF", "ON"])
enable_dev_mem = cycle(["ON", "OFF"])
enable_pmal = cycle(["ON", "OFF"])
save_options = cycle(["", "Saved"])
MAKE_JOBS = 10
main_dir = os.getcwd()


class MenuType(Enum):
    NONE = 0
    MAIN_MENU = 1
    DEBIAN_PACKAGE_MENU = 2


class menuOptions:

    current_environment = next(environments)
    enable_info_logs = "OFF"
    enable_debug_logs = "OFF"
    enable_unit_test = "OFF"
    create_share_library = "OFF"
    create_tool = "ON"
    enable_fast_logs = "ON"
    enable_dev_mem = "OFF"
    enable_pmal = "OFF"
    data_display = "HEXADECIMAL"
    save_preferences = ""
    basic_test = "/" + DefaultPaths.BASIC_TEST
    preferences_path = DefaultPaths.PREFERENCES
    build_path = DefaultPaths.BUILD


def ctrl_handler(signum, frame):
    """Runs when the user presses Ctrl-C"""
    print("Ctrl+C was detected. Exiting program...")
    exit(1)


def _parse_args(argv: List[str]) -> argparse.Namespace:

    parser = argparse.ArgumentParser(description=f"Compile {TOOL_NAME}.")

    parser.add_argument(
        "-e",
        "--environment",
        type=str,
        default=menuOptions.current_environment,
        choices=TargetEnvironment,
        help="Environment target for tool compilation (default: %(default)s).",
    )

    parser.add_argument(
        "-i",
        "--infoLogs",
        action="store_true",
        default=False,
        help="Enable info logs for executable files or Debian package "
        + "(default: %(default)s).",
    )
    parser.add_argument(
        "-d",
        "--debugLogs",
        action="store_true",
        default=False,
        help="Enable debug logs for executable files or Debian package "
        + "(default: %(default)s).",
    )
    parser.add_argument(
        "--enable_devmem",
        action="store_true",
        default=False,
        help="Enables the /dev/mem memory allocator.",
    )
    parser.add_argument(
        "--enable_pmal",
        action="store_true",
        default=False,
        help="Enables the pinned memory allocator.",
    )
    parser.add_argument(
        "-u",
        "--unitTest",
        action="store_true",
        default=False,
        help="Enable a unit test for the tool (default: %(default)s).",
    )

    parser.add_argument(
        "-l",
        "--library",
        action="store_true",
        default=False,
        help="Enable shared library option. Note: This option does not work "
        + "for SHARED_LIBRARY environment (default: %(default)s).",
    )

    parser.add_argument(
        "-t",
        "--tool",
        action="store_true",
        help="Enable tool generation only on LINUX and SVOS "
        + "(default: %(default)s).",
    )

    parser.add_argument(
        "--fastLogs",
        action="store_true",
        help="Enable fast logs (default: %(default)s).",
    )

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default=menuOptions.data_display,
        help="Numeric base format to display data in logs"
        + "(default: %(default)s).",
    )

    preferences = parser.add_argument_group("compilation preferences file")

    preferences.add_argument(
        "-r",
        "--readPreferences",
        action="store_true",
        help="Load saved json preferences file for compiling script.",
    )

    preferences.add_argument(
        "-s",
        "--savePreferences",
        action="store_true",
        default=False,
        help="Save current compilation preferences into a json file.",
    )

    parser.add_argument(
        "--test_path",
        type=str,
        default=menuOptions.basic_test,
        help="Specify the path to the test case file to execute the tool",
    )

    compiling_group = parser.add_mutually_exclusive_group()
    compiling_group.add_argument(
        "-c",
        "--compile",
        action="store_true",
        default=False,
        help="Compile IMC for LINUX, SVOS or ALGORITHM LIBRARY.",
    )
    compiling_group.add_argument(
        "-p",
        "--debianPackage",
        action="store_true",
        default=False,
        help="Build Debian Package.",
    )

    parser.add_argument(
        "--version", "-V", action="version", version=str(__version__)
    )

    parser.add_argument(
        "-v",
        dest="verbosity",
        default=4,
        action=VerboseAction,
        help="Sets available verbosity level. -v off turns off all output to "
        + "the screen.  Default is -vvvv.",
    )
    return parser.parse_args()


def file_exists(abs_path):
    if os.path.isfile(abs_path):
        return "file exists"
    else:
        return "file does not exist"


def _print_subheaders(title, clear_screen):
    header_len = 88

    if clear_screen:
        os.system(("cls" if os.name == "nt" else "clear"))
    padding = int((header_len - len(title)) / 2)
    print("-" * header_len)
    if padding > 0:
        text = ("-" * padding) + title + ("-" * padding)
    else:
        text = title
    print(text)
    print("-" * header_len + "\n")


def _print_menu(menu_type):
    _print_subheaders("IMC compiling wizard", True)
    print(
        """

        Current test case file path         - {0}
        Current preferences file path       - {1}
        Output path                         - {2}

        Customize the compiling options according your preferences:""".format(
            fix_full_path(menuOptions.basic_test),
            fix_full_path(DefaultPaths.PREFERENCES),
            fix_full_path(DefaultPaths.BUILD),
        )
    )

    if menu_type == MenuType.MAIN_MENU:
        print(
            """
            1. Environment                      - {0}
            2. Info Logs                        - {1}
            3. Debug Logs                       - {2}
            4. Unit Test                        - {3}
            5. Library                          - {4}
            6. Create Tool                      - {5}
            7. Fast logs                        - {6}
            8. Enable /dev/mem memory allocator - {7}
            9. Enable PMAL                      - {8}
            10. Displaying data in              - {9} {10}

            11. Load saved preferences          - {11}
            12. Save current preferences        - {12}

            13. Compile IMC and run basic test
            0. Exit

            """.format(
                menuOptions.current_environment,
                menuOptions.enable_info_logs,
                menuOptions.enable_debug_logs,
                menuOptions.enable_unit_test,
                menuOptions.create_share_library,
                menuOptions.create_tool,
                menuOptions.enable_fast_logs,
                menuOptions.enable_dev_mem,
                menuOptions.enable_pmal,
                menuOptions.data_display,
                "(Only HEX if fast logs enabled)",
                "IMC preferences "
                + file_exists(fix_full_path(DefaultPaths.PREFERENCES)),
                menuOptions.save_preferences,
            )
        )
    if menu_type == MenuType.DEBIAN_PACKAGE_MENU:
        print(
            """
            1. Environment                      - {0}

            2. Load saved preferences          - {1}
            3. Save current preferences        - {2}

            4. Build Debian Package
            0. Exit

            """.format(
                menuOptions.current_environment,
                "IMC preferences "
                + file_exists(fix_full_path(DefaultPaths.PREFERENCES)),
                menuOptions.save_preferences,
            )
        )


def _save_old_build():
    status = 0
    user_input = ""
    old_compilation = fix_full_path(DefaultPaths.OLD_BUILD)
    if os.path.exists(fix_full_path(menuOptions.build_path)):
        print("Building files already exist. Creating backup...")
        # Check if old compilations folder exists
        if os.path.exists(old_compilation) is False:
            # create a directory for the old compilations
            process = subprocess.Popen(["mkdir", old_compilation])
            (stdout, stderr) = process.communicate()
        now = datetime.now().strftime("_%d_%m_%Y_%H_%M_%S")
        new_dir = old_compilation + "/old" + now
        print("Saving files to " + new_dir)
        process = subprocess.call(
            "cp -ar {0} {1}".format(
                fix_full_path(menuOptions.build_path), new_dir
            ),
            shell=True,
        )
        print("\n")
    return status


def create_cmake_files(cmakelists):
    build_dir = fix_full_path(DefaultPaths.BUILD)
    if menuOptions.current_environment == "SVOS_DEBIAN_PACKAGE":
        build_cmake = fix_full_path(cmakelists)
    else:
        build_cmake = fix_full_path(DefaultPaths.BUILD_SYSTEM) + cmakelists
    cmake_file = fix_full_path(DefaultPaths.CMAKELISTS)
    os.chdir("{0}".format(os.path.abspath(os.getcwd())))
    # remove the old compiling directory
    process = subprocess.Popen(["rm", "-rf", build_dir])
    (stdout, stderr) = process.communicate()
    # create the new compiling directory
    process = subprocess.Popen(["mkdir", build_dir])
    (stdout, stderr) = process.communicate()
    # remove the old CMakeLists
    process = subprocess.Popen(["rm", "-f", cmake_file])
    (stdout, stderr) = process.communicate()

    process = subprocess.call(
        "cp {0} {1}".format(build_cmake, cmake_file), shell=True
    )


def data_format_flags():
    display_command = ""
    if menuOptions.data_display == "HEXADECIMAL":
        display_command = display_command + " -DHEX_DATA_OUTPUT={0}".format(
            "ON"
        )
        display_command = display_command + " -DBIN_DATA_OUTPUT={0}".format(
            "OFF"
        )
        display_command = display_command + " -DDEC_DATA_OUTPUT={0}".format(
            "OFF"
        )
    elif menuOptions.data_display == "BINARY":
        display_command = display_command + " -DHEX_DATA_OUTPUT={0}".format(
            "OFF"
        )
        display_command = display_command + " -DBIN_DATA_OUTPUT={0}".format(
            "ON"
        )
        display_command = display_command + " -DDEC_DATA_OUTPUT={0}".format(
            "OFF"
        )
    elif menuOptions.data_display == "DECIMAL":
        display_command = display_command + " -DHEX_DATA_OUTPUT={0}".format(
            "OFF"
        )
        display_command = display_command + " -DBIN_DATA_OUTPUT={0}".format(
            "OFF"
        )
        display_command = display_command + " -DDEC_DATA_OUTPUT={0}".format(
            "ON"
        )
    else:
        display_command = display_command + " -DHEX_DATA_OUTPUT={0}".format(
            "OFF"
        )
        display_command = display_command + " -DBIN_DATA_OUTPUT={0}".format(
            "OFF"
        )
        display_command = display_command + " -DDEC_DATA_OUTPUT={0}".format(
            "OFF"
        )
    return display_command


def create_cmake_command():

    # Create cmake command flags
    cMakeOptions = "cmake"  # SVOS, LINUX and LINUX_ONLY Environment

    if menuOptions.current_environment != "SHARED_LIBRARY":
        cMakeOptions = cMakeOptions + " -DTARGET_ENVIRONMENT={0}".format(
            menuOptions.current_environment
        )
        cMakeOptions = cMakeOptions + " -DCREATE_LIBRARY={0}".format(
            menuOptions.create_share_library
        )
        cMakeOptions = cMakeOptions + " -DCREATE_TOOL={0}".format(
            menuOptions.create_tool
        )
        cMakeOptions = cMakeOptions + " -DENABLE_UNIT_TEST={0}".format(
            menuOptions.enable_unit_test
        )
        cMakeOptions = cMakeOptions + " -DENABLE_DEVMEM={0}".format(
            menuOptions.enable_dev_mem
        )
        cMakeOptions = cMakeOptions + " -DENABLE_PMAL={0}".format(
            menuOptions.enable_pmal
        )
    cMakeOptions = cMakeOptions + " -DENABLE_INFO_LOGS={0}".format(
        menuOptions.enable_info_logs
    )
    cMakeOptions = cMakeOptions + " -DENABLE_DEBUG_LOGS={0}".format(
        menuOptions.enable_debug_logs
    )
    cMakeOptions = cMakeOptions + " -DENABLE_FAST_LOGS={0}".format(
        menuOptions.enable_fast_logs
    )

    cMakeOptions = cMakeOptions + data_format_flags()
    cMakeOptions = cMakeOptions + " ../"
    print(cMakeOptions)
    os.chdir(fix_full_path(menuOptions.build_path))
    os.system(cMakeOptions)
    print("Done" + "\n")


def processing_test_output(stdout, stderr):
    """Processing test output.

    :return: (String, String)
    """
    stdout = str(stdout)
    stderr = str(stderr)
    stdout = stdout.replace("\\n", "\n").replace("\\t", "\t")
    stderr = stderr.replace("\\n", "\n").replace("\\t", "\t")

    return (stdout, stderr)


def _run_imc_test():
    basic_test = fix_full_path(menuOptions.basic_test)
    bin_path = fix_full_path(DefaultPaths.COMPILED_TOOL_BINARY)
    os.chdir(bin_path)
    if menuOptions.current_environment == "SVOS_DEBIAN_PACKAGE":
        # Use debian package binary
        test = "./" + BinaryNames.DEBIAN_PACKAGE_BINARY
    elif (
        menuOptions.create_tool == "ON"
        and menuOptions.current_environment != "SHARED_LIBRARY"
    ):
        test = "./" + BinaryNames.VERSION_BINARY
    else:
        print("Did not pass the flag for tool generation")
    cmd = [test, basic_test]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    (stdout, stderr) = process.communicate()
    (stdout, stderr) = processing_test_output(stdout, stderr)
    status_code = process.wait()
    print(stdout)
    print(stderr)
    print(f"Test case return value: {status_code}")


def _make_imc():
    os.system(f"make -j{MAKE_JOBS}")
    os.chdir(main_dir)
    cmake_lists = fix_full_path(DefaultPaths.CMAKELISTS)
    build_dir = fix_full_path(DefaultPaths.BUILD)
    cmd = "cp " + cmake_lists + " " + build_dir
    print(cmd)
    process = subprocess.call(cmd, shell=True)
    cmd = "rm " + cmake_lists
    print(cmd)
    process = subprocess.call(cmd, shell=True)


def _move_dpkg_files():
    bin_path = fix_full_path(DefaultPaths.COMPILED_TOOL_BINARY)
    generic_test = fix_full_path("/" + DefaultPaths.GENERIC_TEST)
    licenses_path = fix_full_path(DefaultPaths.LICENSES)
    dpkg_path = fix_full_path(DefaultPaths.BUILD + DefaultPaths.DPKG)
    # Move debian package exec and aux files
    _print_subheaders("Moving debian package  executables", False)
    process = subprocess.Popen(["mv", "intelligentmemorychecker", bin_path])
    (stdout, stderr) = process.communicate()
    process = subprocess.Popen(
        ["mv", "intelligentmemorychecker_debug", bin_path]
    )
    (stdout, stderr) = process.communicate()
    process = subprocess.Popen(
        ["mv", "intelligentmemorychecker_info", bin_path]
    )
    (stdout, stderr) = process.communicate()
    # Move debian package generated files
    _print_subheaders("Moving Debian Package auxiliary files", False)
    process = subprocess.call(
        "mv {0}/*.o {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/.deps/ {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/Makefile.in {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/Makefile {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/aclocal.m4 {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/autom4te.cache/ {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/build-stamp {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/config.guess {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/config.h {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/config.h.in {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/config.log {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/config.status {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/config.sub {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/configure {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/configure-stamp {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/debian/intelligentmemorychecker.debhelper.log {1}".format(
            main_dir, dpkg_path
        ),
        shell=True,
    )
    process = subprocess.call(
        "mv {0}/debian/.debhelper {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/compile {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/debian/intelligentmemorychecker.substvars {1}".format(
            main_dir, dpkg_path
        ),
        shell=True,
    )
    process = subprocess.call(
        "mv {0}/debian/intelligentmemorychecker/ {1}".format(
            main_dir, dpkg_path
        ),
        shell=True,
    )
    process = subprocess.call(
        "mv {0}/debian/files {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/debian/tmp/ {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/depcomp {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/install-sh {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/libtool {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/ltmain.sh {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/m4/ {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/missing {1}".format(main_dir, dpkg_path), shell=True
    )
    process = subprocess.call(
        "mv {0}/stamp-h1 {1}".format(main_dir, dpkg_path), shell=True
    )
    print("Done")
    _print_subheaders("Copying licences and generic test", False)
    process = subprocess.Popen(["cp", f"{generic_test}", f"{bin_path}"])
    process = subprocess.Popen(["cp", "-r", f"{licenses_path}", f"{bin_path}"])


def _build_dpkg():
    os.chdir(main_dir)
    bin_path = fix_full_path(DefaultPaths.COMPILED_TOOL_BINARY)
    generic_test = fix_full_path("/" + DefaultPaths.GENERIC_TEST)
    licenses_path = fix_full_path(DefaultPaths.LICENSES)
    dpkg_path = fix_full_path(DefaultPaths.BUILD + DefaultPaths.DPKG)
    # Make debian package files folder
    process = subprocess.Popen(["mkdir", dpkg_path])
    (stdout, stderr) = process.communicate()
    # Make build folder for binaries
    process = subprocess.Popen(["mkdir", bin_path])
    (stdout, stderr) = process.communicate()
    subprocess.call("dpkg-buildpackage -b", shell=True)
    print("Done")
    _move_dpkg_files()


def compile_imc():
    _print_subheaders("Starting compilation", False)
    # Save old compilation files
    _print_subheaders("Saving old compilation files", False)
    _save_old_build()

    # Create makefiles c make
    _print_subheaders("Creating CMake files", False)
    if menuOptions.current_environment == "SVOS_DEBIAN_PACKAGE":
        cmakelists = DefaultPaths.CMAKE_DEBIAN_PACKAGE
    elif menuOptions.current_environment == "SHARED_LIBRARY":
        cmakelists = DefaultPaths.CMAKE_LIBRARY
    else:
        cmakelists = DefaultPaths.CMAKE_SCRIPT
    create_cmake_files(cmakelists)  # includes the mkdir of the /build

    if menuOptions.current_environment == "SVOS_DEBIAN_PACKAGE":
        # Start the building for Debian package
        os.chdir(main_dir)
        _print_subheaders("Building Debian Package", False)
        _build_dpkg()
    else:
        create_cmake_command()
        _print_subheaders("Compiling - Make", False)
        _make_imc()
    # Run basic / generic IMC test
    if menuOptions.current_environment != "SHARED_LIBRARY":
        # Run basic IMC test case
        _print_subheaders("Running basic IMC test", False)
        # Verify that binaries were successfully generated into build folder
        _verify_binaries()
        _run_imc_test()
    else:
        print(
            f"[IMC-Info] Finished compilation for "
            + f"{menuOptions.current_environment}"
        )
    # Return to main directory
    os.chdir(main_dir)


def load_preferences():
    status = ExitCode.OK
    print("Loading IMC compiling preferences files.")
    try:
        with open(fix_full_path(menuOptions.preferences_path)) as json_file:
            data = json.load(json_file)
            for imc in data["IMC"]:
                menuOptions.current_environment = imc["TARGET_ENVIRONMENT"]
                menuOptions.enable_info_logs = imc["INFO_LOGS"]
                menuOptions.enable_debug_logs = imc["DEBUG_LOGS"]
                menuOptions.enable_unit_test = imc["UNIT_TEST"]
                menuOptions.create_share_library = imc["CREATE_SHARE_LIBRARY"]
                menuOptions.create_tool = imc["CREATE_TOOL"]
                menuOptions.enable_fast_logs = imc["FAST_LOGS"]
                menuOptions.enable_dev_mem = imc["ENABLE_DEVMEM"]
                menuOptions.enable_pmal = imc["ENABLE_PMAL"]
    except IOError as e:
        print(
            """Could not open the IMC preferences compiling file.
        I/O error({0}): {1}""".format(
                e.errno, e.strerror
            )
        )
        user_input = str(input("Press 0 to return to main menu: "))
        if user_input == "0":
            return status
    except Exception as e:
        status = ExitCode.UNKNOWN_STATUS_CODE
        print("Unexpected error: {0}".format(e))
        raise
    return status


def save_preferences():
    status = ExitCode.OK
    data = {}
    data["IMC"] = []
    data["IMC"].append(
        {
            "TARGET_ENVIRONMENT": "{0}".format(menuOptions.current_environment),
            "INFO_LOGS": "{0}".format(menuOptions.enable_info_logs),
            "DEBUG_LOGS": "{0}".format(menuOptions.enable_debug_logs),
            "UNIT_TEST": "{0}".format(menuOptions.enable_unit_test),
            "CREATE_SHARE_LIBRARY": "{0}".format(
                menuOptions.create_share_library
            ),
            "CREATE_TOOL": "{0}".format(menuOptions.create_tool),
            "FAST_LOGS": "{0}".format(menuOptions.enable_fast_logs),
            "ENABLE_DEVMEM": "{0}".format(menuOptions.enable_dev_mem),
            "ENABLE_PMAL": "{0}".format(menuOptions.enable_pmal),
            "DISPLAY_DATA_IN": "{0}".format(menuOptions.data_display),
        }
    )
    try:
        with open(fix_full_path(DefaultPaths.PREFERENCES), "w") as outfile:
            json.dump(data, outfile, indent=4)
    except IOError as e:
        print(
            """
        Could not open the IMC preferences file! Please,
        try again or close the preferences file.
        I/O error({0}): {1}
         """.format(
                e.errno, e.strerror
            )
        )
        user_input = str(input("Press 0 to return to main menu: "))
        if user_input == "0":
            return status
    return status


def _print_intel_logo():
    print(INTEL_LOGO)


def _iterate_options(current_menu):
    user_input = str(input("Choose the number to change the current value: "))
    menu_type = current_menu
    if user_input == "0":
        menu_type = MenuType.NONE
        _print_intel_logo()
    if user_input == "1":
        menuOptions.current_environment = next(environments)
        # If environment is debian package show only debian package menu
        if menuOptions.current_environment == TargetEnvironment[3]:
            menu_type = MenuType.DEBIAN_PACKAGE_MENU
        else:
            menu_type = MenuType.MAIN_MENU
        if menuOptions.current_environment == "SHARED_LIBRARY":
            # Disable options when changing to menu for algorithm
            menuOptions.create_share_library = "OFF"
            menuOptions.create_tool = "OFF"
        else:
            # Enable options tool creation when changing from algorithm
            # Create share_library is disabled by default
            menuOptions.create_tool = "ON"
    if user_input == "2":
        if menu_type == MenuType.DEBIAN_PACKAGE_MENU:
            load_preferences()
        else:
            menuOptions.enable_info_logs = next(info_logs)
    if user_input == "3":
        if menu_type == MenuType.DEBIAN_PACKAGE_MENU:
            save_preferences()
        else:
            menuOptions.enable_debug_logs = next(debug_logs)
    if user_input == "4":
        if menu_type == MenuType.DEBIAN_PACKAGE_MENU:
            compile_imc()
            user_input = str(input("Press any key to continue: "))
        else:
            menuOptions.enable_unit_test = next(unit_test)
    if user_input == "5":
        if menuOptions.current_environment != "SHARED_LIBRARY":
            menuOptions.create_share_library = next(library)
        else:
            # Option disabled for algorithm library
            menuOptions.create_share_library = "OFF"
    if user_input == "6":
        if menuOptions.current_environment != "SHARED_LIBRARY":
            menuOptions.create_tool = next(tool)
        else:
            # Option disabled for algorithm library
            menuOptions.create_tool = "OFF"
    if user_input == "7":
        menuOptions.enable_fast_logs = next(fast_logs)
        if menuOptions.enable_fast_logs == "ON":
            menuOptions.data_display = "HEXADECIMAL"
    if user_input == "8":
        menuOptions.enable_dev_mem = next(enable_dev_mem)
    if user_input == "9":
        menuOptions.enable_pmal = next(enable_pmal)
    if user_input == "10":
        if menuOptions.enable_fast_logs == "OFF":
            menuOptions.data_display = next(data_display)
        if menuOptions.enable_fast_logs == "ON":
            menuOptions.data_display = "HEXADECIMAL"
    if user_input == "11":
        load_preferences()
    if user_input == "12":
        menuOptions.save_preferences = next(save_options)
        save_preferences()
    if user_input == "13":
        compile_imc()
        user_input = str(input("Press any key to continue: "))
    return menu_type


def _check_parsed_options(parsed_args):
    """
    Check command line inputs

    """
    if parsed_args.readPreferences:
        print(menuOptions.preferences_path)
        user_input = str(input("Press 1 to continue executing IMC test: "))
        if os.path.isfile(fix_full_path(menuOptions.preferences_path)):
            load_preferences()
        else:
            print("There is not an IMC preferences file for compiling options.")
    else:
        menuOptions.current_environment = parsed_args.environment

        menuOptions.enable_info_logs = "ON" if parsed_args.infoLogs else "OFF"
        menuOptions.enable_debug_logs = "ON" if parsed_args.debugLogs else "OFF"
        menuOptions.enable_unit_test = "ON" if parsed_args.unitTest else "OFF"
        if parsed_args.library:
            menuOptions.create_share_library = "ON"
        else:
            menuOptions.create_share_library = "OFF"
        menuOptions.create_tool = "ON" if parsed_args.tool else "OFF"
        menuOptions.enable_fast_logs = "ON" if parsed_args.fastLogs else "OFF"
        if parsed_args.enable_devmem:
            menuOptions.enable_dev_mem = "ON"
        else:
            menuOptions.enable_dev_mem = "OFF"
        menuOptions.enable_pmal = "ON" if parsed_args.enable_pmal else "OFF"
        menuOptions.data_display = parsed_args.format
        menuOptions.basic_test = "/" + parsed_args.test_path
        print(menuOptions.basic_test)

        if parsed_args.savePreferences:
            print("Saving preferences into " + menuOptions.preferences_path)
            save_preferences()
    return 0


def _verify_binaries():
    bin_path = fix_full_path(DefaultPaths.COMPILED_TOOL_BINARY)
    if menuOptions.current_environment == "SVOS_DEBIAN_PACKAGE":
        # Check for binaries
        binaries = [
            "intelligentmemorychecker",
            "intelligentmemorychecker_debug",
            "intelligentmemorychecker_info",
        ]
    if (
        menuOptions.current_environment == "LINUX"
        or menuOptions.current_environment == "SVOS"
    ):
        binaries = [BinaryNames.VERSION_BINARY]
    for bin in binaries:
        if not os.access(bin_path + bin, os.F_OK, follow_symlinks=True):
            raise ValueError(
                f"The path to the binary does not appear to be correct!"
            )


def main():
    """
    Main entry point for starting the Intelligent Memory Checker compiler
    instance.

    """
    parsed_args = _parse_args(sys.argv[1:])
    if parsed_args.compile:
        _check_parsed_options(parsed_args)
        compile_imc()
        _print_intel_logo()
    else:
        # Verify menu for parsed options
        if menuOptions.current_environment == "SVOS_DEBIAN_PACKAGE":
            current_menu = MenuType.DEBIAN_PACKAGE_MENU
        else:
            current_menu = MenuType.MAIN_MENU
        while current_menu != MenuType.NONE:
            _print_menu(current_menu)
            current_menu = _iterate_options(current_menu)


if __name__ == "__main__":
    main()
