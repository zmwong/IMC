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

from scripts.bin import imc_runner
import sys
import os


def runIMC(argv=None):
    """Programmatic entrypoint for the IMC runner.

    Args:
            argv: list of command-line arguments (equivalent to sys.argv[1:]).
                      If None, an empty list is used.

    Returns:
            The return value from imc_runner.main(argv) if any.
    """
    root_directory = os.path.dirname(os.path.abspath(__file__))
    os.environ["PROJECT_ROOT"] = root_directory

    if argv is None:
        argv = []

    try:
        return imc_runner.main(argv)
    except SystemExit as se:
        # imc_runner and other components may call sys.exit() via LogManagerThread.pretty_exit()
        # Catch it here so callers can invoke runIMC multiple times without the whole process exiting.
        code = se.code
    try:
        return int(code) if code is not None else 1
    except Exception:
        return 1


if __name__ == "__main__":
    # Preserve previous behavior when executed as a script.
    sys.exit(runIMC(sys.argv[1:]))
