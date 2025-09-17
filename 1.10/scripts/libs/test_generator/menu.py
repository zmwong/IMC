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

"""
This module is a Python wrapper for generating a XML file via command
line menu
"""
import os
import sys
from scripts.libs.test_generator import generator_main
from scripts.libs.test_generator.cli_menus import MenuContext
from scripts.libs.test_generator.cli_menus import FlowQuantityMenu
from scripts.libs.definitions.imc import TOOL_NAME
from scripts.libs.loggers.log_manager import (
    LogManager,
    LogManagerThread,
)


# Check python version is valid up from 3.6
if not sys.version_info[0:2] >= (3, 6):
    print(f"This module requires Python 3.6 or newer.")


def _print_subheaders(clear_screen):
    """Print the title and instructions of the current menu."""

    # Get menu header values to display.
    (title, menu_text) = MenuContext().get_current_menu().menu_strings.value
    header_len = 79

    if clear_screen:
        os.system(("cls" if os.name == "nt" else "clear"))
    padding = int((header_len - len(title)) / 2)
    LogManager().log(
        "SYS",
        LogManagerThread.Level.INFO,
        "-" * header_len,
    )
    if padding > 0:
        text = ("-" * padding) + title + ("-" * padding)
    else:
        text = title
    LogManager().log("SYS", LogManagerThread.Level.INFO, text)
    if MenuContext()._get_test_number() >= 1:
        LogManager().log(
            "SYS",
            LogManagerThread.Level.INFO,
            f"{'-' * padding} Test number: {MenuContext()._get_test_number()} {'-' * padding}",
        )
    else:
        LogManager().log(
            "SYS",
            LogManagerThread.Level.INFO,
            "-" * header_len,
        )

    LogManager().log(
        "SYS",
        LogManagerThread.Level.INFO,
        f"{' ' * 9}{menu_text}",
    )


def _run_menu():
    """Verifies current menu, and handles the output/input it should give."""
    menu = MenuContext().get_current_menu()
    _print_subheaders(True)

    menu.menu_action()


def generate_tests_via_menu():
    """Main entry point for starting the XML Generator CLI instance."""
    menu = MenuContext(FlowQuantityMenu())

    while menu.get_current_menu() is not None:
        _run_menu()

    return menu.saved_tests


def generator_main():
    """Main entry point for starting the XML Generator CLI instance."""
    menu = MenuContext(FlowQuantityMenu())

    while menu.get_current_menu() is not None:
        _run_menu()

    LogManager().log(
        "SYS",
        LogManagerThread.Level.INFO,
        "Generating tests.",
    )
    generator_main.generate_tests(menu.tests_output)
    LogManager().log(
        "SYS",
        LogManagerThread.Level.INFO,
        "Tests generated.",
    )


if __name__ == "__main__":
    generator_main()
