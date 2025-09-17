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

""" This module supports the edac error provider."""

import subprocess  # nosec
from typing import List, Optional

from scripts.libs.definitions.errors import (
    ErrorEntry,
    ErrorType,
    ErrorProviderNotFound,
)
from scripts.libs.definitions.errors import DEV_MODE  # LOD (imc_internal)
from scripts.libs.errors.providers.provider import BaseProvider


class EDACErrorEntry(ErrorEntry):
    """Representation of an error reported by edac-util"""

    # pylint: disable=too-many-instance-attributes
    DIMM_LABEL_ENTRY_COUNT = 5
    DIMM_LABEL_DELIMITER = "#"
    ERROR_TYPES = {"CE": ErrorType.Correctable, "UE": ErrorType.Uncorrectable}

    @staticmethod
    def get_dimm_item_id(item: str) -> int:
        """Parses and returns the item ID associated with a DIMM label.

        Example (CPU_SrcID#0_MC#1_Chan#0_DIMM#0)
            EDACErrorEntry.get_dimm_item_id('MC#1') -> int(1)

        :param item: Item entry to split
        :return: int
        """
        parts = item.split(EDACErrorEntry.DIMM_LABEL_DELIMITER)
        if not len(parts) == 2:
            raise ValueError("DIMM label did not match expected format.")
        return int(parts[1])

    def __init__(self, row_data: List[str]):
        """Constructor

        :param row_data: List of row items representing an error entry
        """
        super().__init__()

        self._parse_row_data(row_data)

    def __str__(self) -> str:
        """String operator

        :return: str
        """
        plurality = "s" if self.count != 1 else ""
        if self.socket is not None:
            return "".join(
                [
                    f"{self.error_type} memory error{plurality} ",
                    f"({self.count}) on socket {self.socket}, ",
                    f"controller {self.mc}, channel {self.channel}, ",
                    f"and slot {self.slot}",
                ]
            )
        return "".join(
            [
                f"{self.error_type} memory error{plurality} ",
                f"({self.count}) on {self.dimm_label}, controller ",
                f"{self.mc}, and chip select {self.chip_select}",
            ]
        )

    def __repr__(self) -> str:
        """Repr operator

        :return: str
        """
        if self.socket is not None:
            return "".join(
                [
                    f"<EDACErrorEntry(error_type={self.error_type}, ",
                    f"count={self.count}, socket={self.socket}, ",
                    f"mc={self.mc}, channel={self.channel}, ",
                    f"slot={self.slot})>",
                ]
            )
        return "".join(
            [
                f"<EDACErrorEntry(error_type={self.error_type}, ",
                f"count={self.count}, mc={self.mc}, ",
                f"cs={self.chip_select}, ",
                f"dimm_label={self.dimm_label})>",
            ]
        )

    def __eq__(self, other: ErrorEntry) -> bool:
        """Equality operator

        :param other: Other error entry to compare against
        :return: bool
        """
        return self.raw == other.raw

    def __hash__(self) -> int:
        """Hash operator

        :return: int
        """
        return hash((self.raw,))

    def _update_dimm_details(self, dimm_label: str):
        """
        Helper function to update the dimm details if the label has a
        specific number of elements.

        :param dimm_label: The string of the dimm info
        :return: None
        """
        dimm_details = dimm_label.split("_")
        if len(dimm_details) == EDACErrorEntry.DIMM_LABEL_ENTRY_COUNT:
            _, cpu, memctlr, chan, dimm = dimm_details
            self.socket = EDACErrorEntry.get_dimm_item_id(cpu)
            self.mc = EDACErrorEntry.get_dimm_item_id(memctlr)
            self.channel = EDACErrorEntry.get_dimm_item_id(chan)
            self.slot = EDACErrorEntry.get_dimm_item_id(dimm)

    def _parse_row_data(self, row_data: List[str]):
        """Processes the individual error entry items into our structure

        :param row_data: List of error entry items
        :return: None
        """
        mc_id, cs_id, dimm_label, error_type, error_count = row_data

        self.mc = mc_id
        self.chip_select = cs_id
        self.error_type = EDACErrorEntry.ERROR_TYPES.get(
            error_type, ErrorType.Unknown
        )
        self.count = error_count
        self.dimm_label = dimm_label
        self.raw = EDACProvider.RESULT_ROW_DELIMITER.join(row_data)
        self._update_dimm_details(dimm_label)


class EDACProvider(BaseProvider):
    """Error provider for extracting errors from edac-util"""

    COMMAND_NAME = "edac-util"
    COMMAND_PARAMETERS = ["-rfull"]
    RESULT_ROW_ITEM_COUNT = 5
    RESULT_ROW_DELIMITER = ":"

    def __init__(self, path: Optional[str] = None):
        """Constructor

        :param path: Optional path to the edac-util command
        """
        if not path:
            path = EDACProvider.COMMAND_NAME

        super().__init__(path=path)
        self.command_line_arguments = EDACProvider.COMMAND_PARAMETERS

    def _self_test(self):
        """
        A test to verify that edac-util exists and that it detects memory
        controllers.

        :return: None
        """
        timeout = 10
        try:
            if (
                subprocess.run(
                    ["which", EDACProvider.COMMAND_NAME],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                ).returncode
                != 0
            ):  # nosec
                raise ErrorProviderNotFound(
                    f"Could not find {EDACProvider.COMMAND_NAME}; please "
                    + "confirm it's in your path."
                )
            if (
                subprocess.run(
                    [EDACProvider.COMMAND_NAME, "-s"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                ).returncode
                != 0
            ):  # nosec
                raise ErrorProviderNotFound(
                    f"{EDACProvider.COMMAND_NAME} could not find any memory "
                    + "controllers; please confirm that the edac module, "
                    + "or driver, is valid."
                )
        except subprocess.TimeoutExpired as ex_err:
            raise ErrorProviderNotFound(
                f"{EDACProvider.COMMAND_NAME} took longer than {timeout} "
                + "to run. Aborting its usage."
            ) from ex_err
        except subprocess.SubprocessError as ex_err:
            raise ErrorProviderNotFound(
                "An unexpected error occurred while initializing the edac "
                + "error provider."
            ) from ex_err

    def init(self):
        """ Provider initialization - verifies that the command is in the path \
            and that memory controllers are found.

        :return: None
        """
        self._self_test()

    def get_errors(self) -> List[EDACErrorEntry]:
        """Retrieve a list of errors from the provider

        :return: List of EDACErrorEntry
        """
        errors = []

        results = self._execute()
        for row in results:
            row_data = row.split(EDACProvider.RESULT_ROW_DELIMITER)
            if len(row_data) != EDACProvider.RESULT_ROW_ITEM_COUNT:
                continue
            try:
                # count is the last element in the row data
                error_count = int(row_data[-1:][0])
            except (ValueError, IndexError):
                error_count = 1  # the count value couldn't be converted to int
            if error_count > 0:
                errors.append(EDACErrorEntry(row_data))

        return errors

    def clear(self):
        """Clear errors - unused

        :return: None
        """
        return None

    def _execute(self) -> List[str]:
        """Executes the provider command in order to retrieve the errors

        :return: List of strings
        """
        results = []

        try:
            # nosec
            with subprocess.Popen(
                [self.path] + self.command_line_arguments,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            ) as proc:
                with proc.stdout:
                    for line in iter(proc.stdout.readline, b""):
                        results.append(bytes.decode(line).strip())

        except FileNotFoundError as ex_err:
            raise ErrorProviderNotFound(
                f"Could not find {EDACProvider.COMMAND_NAME}; "
                + "please confirm it's in your path."
            ) from ex_err

        return results


# LOD (imc_internal)
if DEV_MODE:

    class FakeEDACProvider(EDACProvider):
        """Fake EDAC provider for testing purposes"""

        import os  # pylint: disable=import-outside-toplevel

        FAKE_LOG_FILE = os.path.join(os.path.dirname(__file__), "fake_edac.log")

        def __init__(self, path: str = None):
            super().__init__(path=path)
            self._counter = 0
            self._fake_error = True

        def init(self):
            """
            Provider initialization - this method bypasses any utility or sysfs
            init.
            :return: None
            """
            return None

        def get_errors(self) -> List[EDACErrorEntry]:
            errors = super().get_errors()

            # Fake an error on the first entry if this is the second pass.
            if self._fake_error and self._counter >= 1:
                errors[0].raw = "foobar"
            else:
                self._counter += 1

            return errors

        def _execute(self) -> List[str]:
            with open(
                FakeEDACProvider.FAKE_LOG_FILE, "r", encoding="utf-8"
            ) as f_h:
                return [line.strip() for line in f_h.readlines()]


# LOD END
