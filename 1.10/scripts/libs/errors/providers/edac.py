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

import os
import subprocess  # nosec
import re
import glob
from typing import List, Optional

from scripts.libs.definitions.errors import (
    ErrorEntry,
    ErrorType,
    ErrorProviderNotFound,
)

from scripts.libs.errors.providers.provider import BaseProvider
from scripts.libs.loggers.log_manager import LogManager, LogManagerThread


class EDACErrorEntry(ErrorEntry):
    """Representation of a memory error detected from kernel EDAC interfaces"""

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

    def __init__(self, row_data: List[str], thread_id: str = None):
        """Constructor

        :param row_data: List of row items representing an error entry
        :param thread_id: Optional thread ID that triggered this error
        """
        super().__init__()

        # Store thread association
        self.thread_id = thread_id or "Unknown"

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
        self.raw = "|".join(row_data)
        self._update_dimm_details(dimm_label)


class EDACProvider(BaseProvider):
    """Error provider for extracting memory errors from kernel EDAC interfaces (dmesg/sysfs)"""

    def __init__(self, path: Optional[str] = None):
        """Constructor

        :param path
        """
        super().__init__(path=None)

    def init(self):
        """Provider initialization - validates EDAC kernel subsystem availability.

        :return: None
        """
        self._validate_edac_installation()

    def _validate_edac_installation(self):
        """
        Validation of EDAC kernel subsystem installation and configuration.

        :return: None
        """
        validation_errors = []
        # Check if EDAC kernel modules are loaded
        try:
            result = subprocess.run(
                ["lsmod"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lsmod_output = result.stdout.lower()
                if "edac" not in lsmod_output:
                    validation_errors.append(
                        "No EDAC related modules are loaded. Please ensure EDAC drivers are installed and loaded."
                    )
            else:
                validation_errors.append(
                    "Cannot check kernel modules (lsmod failed)"
                )
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ):
            validation_errors.append(
                "Cannot check kernel modules (lsmod unavailable)"
            )

        # Check if EDAC sysfs interface exists
        edac_sysfs_path = "/sys/devices/system/edac"
        if not os.path.exists(edac_sysfs_path):
            validation_errors.append(
                f"EDAC sysfs interface not found at {edac_sysfs_path}. "
                "EDAC subsystem may not be properly initialized."
            )

        # Check if memory controllers are detected
        try:
            mc_dirs = glob.glob("/sys/devices/system/edac/mc/mc*")
            if not mc_dirs:
                validation_errors.append(
                    "No memory controllers detected by EDAC subsystem. "
                    "This may indicate incompatible hardware or missing EDAC drivers."
                )
        except (OSError, PermissionError):
            validation_errors.append(
                "Cannot access EDAC memory controller information"
            )

        if validation_errors:
            validation_errors.append(
                "Warning: EDAC is only available on Linux systems."
            )
            error_message = "EDAC subsystem validation failed:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            error_message += (
                "\n\nTo resolve this issue:\n"
                "  1. Ensure EDAC kernel modules are loaded: 'lsmod | grep edac'\n"
                "  2. Check if your hardware supports EDAC error detection\n"
                "  3. Verify EDAC drivers are installed for your memory controller\n"
                "  4. Run with appropriate permissions to access kernel interfaces"
            )

            raise ErrorProviderNotFound(error_message)

    def get_errors(self) -> List[EDACErrorEntry]:
        """
        Memory error detection using direct kernel interfaces (dmesg and sysfs).
        This implementation provides comprehensive error detection.

        :return: List of EDACErrorEntry with error information
        """
        errors = []

        try:
            errors = self._get_errors_from_dmesg()
            if errors:
                return errors
        except (subprocess.SubprocessError, OSError, IOError) as e:
            # Log warning if dmesg access fails but continue with sysfs
            LogManager().log(
                "MEMORY",
                LogManagerThread.Level.WARNING,
                f"Failed to read memory errors from dmesg: {str(e)}",
            )

        try:
            errors = self._get_errors_from_sysfs()
            if errors:
                return errors
        except (OSError, IOError, PermissionError) as e:
            # Log warning if sysfs access fails
            LogManager().log(
                "MEMORY",
                LogManagerThread.Level.WARNING,
                f"Failed to read memory errors from sysfs: {str(e)}",
            )
        return errors

    def _get_errors_from_dmesg(self) -> List[EDACErrorEntry]:
        """
        Enhanced dmesg parsing for memory errors with recent timestamp focus.

        :return: List of EDACErrorEntry from dmesg
        """
        errors = []

        try:
            try:
                result = subprocess.run(
                    ["dmesg", "-T"], capture_output=True, text=True, timeout=10
                )
            except FileNotFoundError:
                # dmesg with timestamps not available
                result = subprocess.run(
                    ["dmesg"], capture_output=True, text=True, timeout=5
                )

            if result.returncode != 0:
                return errors

            lines = result.stdout.split("\n")

            recent_lines = lines[-100:] if len(lines) > 100 else lines

            for line in recent_lines:
                if self._is_memory_error_line(line):
                    error = self._parse_dmesg_line(line)
                    if error:
                        errors.append(error)

            for line in lines:
                if "Hardware Error" in line or "Machine check" in line:
                    error = self._parse_dmesg_line(line)
                    if error and error not in errors:
                        errors.append(error)

            return errors

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            # Log error if dmesg command times out or fails
            LogManager().log(
                "MEMORY",
                LogManagerThread.Level.ERROR,
                f"dmesg command failed or timed out: {str(e)}",
            )
            return []

    def _is_memory_error_line(self, line: str) -> bool:
        """Check if line contains memory error info."""
        line_lower = line.lower()
        return any(
            keyword in line_lower
            for keyword in [
                "edac mc",
                "correctable",
                "uncorrectable",
                "memory error",
                "hardware error",
                "machine check events",
                "mce:",
                "ce memory",
                "ue memory",
            ]
        )

    def _parse_dmesg_line(self, line: str) -> Optional[EDACErrorEntry]:
        """Enhanced dmesg line parsing for detailed memory error information."""
        try:
            edac_detailed_pattern = r"EDAC MC(\d+):\s*(\d+)\s*(CE|UE)\s+memory.*?(?:Row:0x([a-fA-F0-9]+)|Row:(\d+)).*?(?:Column:0x([a-fA-F0-9]+)|Column:(\d+)).*?(?:Bank:0x([a-fA-F0-9]+)|Bank:(\d+)).*?(?:BankGroup:0x([a-fA-F0-9]+)|BankGroup:(\d+)).*?SystemAddress:0x([a-fA-F0-9]+)"

            debug_pattern = r"EDAC DEBUG:.*?SystemAddress:0x([a-fA-F0-9]+).*?MemoryControllerId:0x(\d+).*?ChannelId:0x(\d+).*?Row:0x([a-fA-F0-9]+).*?Column:0x([a-fA-F0-9]+).*?Bank:0x([a-fA-F0-9]+).*?BankGroup:0x([a-fA-F0-9]+)"
            standard_pattern = (
                r"EDAC MC(\d+):\s*(\d+)\s*(CE|UE|Correctable|Uncorrectable)"
            )

            detailed_match = re.search(
                edac_detailed_pattern, line, re.IGNORECASE
            )
            if detailed_match:
                mc_id = detailed_match.group(1)
                count = detailed_match.group(2)
                error_type = (
                    "CE" if detailed_match.group(3).upper() == "CE" else "UE"
                )

                # Extract detailed memory topology
                row = detailed_match.group(4) or detailed_match.group(5) or "0"
                column = (
                    detailed_match.group(6) or detailed_match.group(7) or "0"
                )
                bank = detailed_match.group(8) or detailed_match.group(9) or "0"
                bank_group = (
                    detailed_match.group(10) or detailed_match.group(11) or "0"
                )
                system_address = detailed_match.group(12)

                # Create enhanced error entry
                return self._create_enhanced_error_entry(
                    mc_id,
                    count,
                    error_type,
                    line,
                    row=row,
                    column=column,
                    bank=bank,
                    bank_group=bank_group,
                    system_address=system_address,
                )

            debug_match = re.search(debug_pattern, line, re.IGNORECASE)
            if debug_match and "EDAC DEBUG" in line:
                system_address = debug_match.group(1)
                mc_id = debug_match.group(2)
                channel_id = debug_match.group(3)
                row = debug_match.group(4)
                column = debug_match.group(5)
                bank = debug_match.group(6)
                bank_group = debug_match.group(7)

                # Determine error type
                error_type = (
                    "CE"
                    if "CE memory" in line or "Correctable" in line
                    else "UE"
                )
                count = "1"

                return self._create_enhanced_error_entry(
                    mc_id,
                    count,
                    error_type,
                    line,
                    row=row,
                    column=column,
                    bank=bank,
                    bank_group=bank_group,
                    system_address=system_address,
                    channel_id=channel_id,
                )

            standard_match = re.search(standard_pattern, line, re.IGNORECASE)
            if standard_match:
                mc_id = (
                    standard_match.group(1)
                    if standard_match.group(1).isdigit()
                    else "0"
                )
                count = (
                    standard_match.group(2)
                    if standard_match.group(2).isdigit()
                    else "1"
                )
                error_type = standard_match.group(3)

                if error_type.lower() in ["ce", "correctable"]:
                    error_type = "CE"
                elif error_type.lower() in ["ue", "uncorrectable"]:
                    error_type = "UE"

                row = column = bank = bank_group = system_address = None

                addr_match = re.search(r"SystemAddress:0x([a-fA-F0-9]+)", line)
                row_match = re.search(r"Row:0x([a-fA-F0-9]+)", line)
                col_match = re.search(r"Column:0x([a-fA-F0-9]+)", line)
                bank_match = re.search(r"Bank:0x([a-fA-F0-9]+)", line)
                bg_match = re.search(r"BankGroup:0x([a-fA-F0-9]+)", line)

                if addr_match:
                    system_address = addr_match.group(1)
                if row_match:
                    row = row_match.group(1)
                if col_match:
                    column = col_match.group(1)
                if bank_match:
                    bank = bank_match.group(1)
                if bg_match:
                    bank_group = bg_match.group(1)

                return self._create_enhanced_error_entry(
                    mc_id,
                    count,
                    error_type,
                    line,
                    row=row,
                    column=column,
                    bank=bank,
                    bank_group=bank_group,
                    system_address=system_address,
                )

            return None

        except (ValueError, AttributeError) as e:
            # Return None if line parsing fails due to unexpected format
            return None

    def _create_enhanced_error_entry(
        self, mc_id, count, error_type, raw_line, **details
    ):
        """Create an enhanced EDACErrorEntry with detailed information."""
        try:
            dimm_label = f"CPU_SrcID#0_MC#{mc_id}_Chan#0_DIMM#0"
            thread_id = self._determine_thread_id(mc_id, dimm_label)

            row_data = [mc_id, "0", dimm_label, error_type, str(count)]
            error_entry = EDACErrorEntry(row_data, thread_id)
            error_entry.raw = raw_line.strip()

            if details.get("row"):
                try:
                    row_val = details["row"]
                    if isinstance(row_val, str):
                        if row_val.startswith("0x"):
                            error_entry.row = int(row_val, 16)
                        else:
                            try:
                                error_entry.row = int(row_val, 16)
                            except ValueError:
                                error_entry.row = int(row_val)
                    else:
                        error_entry.row = int(row_val)
                except (ValueError, TypeError):
                    # Keep original value if conversion fails
                    error_entry.row = details["row"]

            if details.get("column"):
                try:
                    col_val = details["column"]
                    if isinstance(col_val, str):
                        if col_val.startswith("0x"):
                            error_entry.column = int(col_val, 16)
                        else:
                            try:
                                error_entry.column = int(col_val, 16)
                            except ValueError:
                                error_entry.column = int(col_val)
                    else:
                        error_entry.column = int(col_val)
                except (ValueError, TypeError):
                    # Keep original value if conversion fails
                    error_entry.column = details["column"]

            if details.get("bank"):
                try:
                    bank_val = details["bank"]
                    if isinstance(bank_val, str):
                        if bank_val.startswith("0x"):
                            error_entry.bank = int(bank_val, 16)
                        else:
                            try:
                                error_entry.bank = int(bank_val, 16)
                            except ValueError:
                                error_entry.bank = int(bank_val)
                    else:
                        error_entry.bank = int(bank_val)
                except (ValueError, TypeError):
                    # Keep original value if conversion fails
                    error_entry.bank = details["bank"]

            if details.get("bank_group"):
                try:
                    bg_val = details["bank_group"]
                    if isinstance(bg_val, str):
                        if bg_val.startswith("0x"):
                            error_entry.bank_group = int(bg_val, 16)
                        else:
                            try:
                                error_entry.bank_group = int(bg_val, 16)
                            except ValueError:
                                error_entry.bank_group = int(bg_val)
                    else:
                        error_entry.bank_group = int(bg_val)
                except (ValueError, TypeError):
                    # Keep original value if conversion fails
                    error_entry.bank_group = details["bank_group"]

            if details.get("system_address"):
                error_entry.system_address = details["system_address"]

            if details.get("channel_id"):
                error_entry.channel_id = details["channel_id"]

            # Add page and virtual address if available
            if details.get("page"):
                error_entry.page = details["page"]
            if details.get("virtual_address"):
                error_entry.virtual_address = details["virtual_address"]

            return error_entry if int(count) > 0 else None

        except AttributeError as e:
            # Return None if error entry creation fails due to missing attributes
            return None

    def _get_errors_from_sysfs(self) -> List[EDACErrorEntry]:
        """
        Simple sysfs error count reading.

        :return: List of EDACErrorEntry from sysfs
        """
        errors = []

        try:
            mc_dirs = glob.glob("/sys/devices/system/edac/mc/mc*")

            for mc_dir in mc_dirs:
                mc_num = os.path.basename(mc_dir)[2:]

                # Check CE count
                ce_file = os.path.join(mc_dir, "ce_count")
                if os.path.exists(ce_file):
                    try:
                        with open(ce_file, "r") as f:
                            ce_count = int(f.read().strip())
                        if ce_count > 0:
                            dimm_label = (
                                f"CPU_SrcID#0_MC#{mc_num}_Chan#0_DIMM#0"
                            )
                            thread_id = self._determine_thread_id(
                                mc_num, dimm_label
                            )
                            row_data = [
                                mc_num,
                                "0",
                                dimm_label,
                                "CE",
                                str(ce_count),
                            ]
                            error_entry = EDACErrorEntry(row_data, thread_id)
                            error_entry.detection_source = "sysfs"
                            errors.append(error_entry)
                    except (ValueError, IOError) as e:
                        # Skip this file if count cannot be read or converted
                        pass

                # Check UE count
                ue_file = os.path.join(mc_dir, "ue_count")
                if os.path.exists(ue_file):
                    try:
                        with open(ue_file, "r") as f:
                            ue_count = int(f.read().strip())
                        if ue_count > 0:
                            dimm_label = (
                                f"CPU_SrcID#0_MC#{mc_num}_Chan#0_DIMM#0"
                            )
                            thread_id = self._determine_thread_id(
                                mc_num, dimm_label
                            )
                            row_data = [
                                mc_num,
                                "0",
                                dimm_label,
                                "UE",
                                str(ue_count),
                            ]
                            error_entry = EDACErrorEntry(row_data, thread_id)
                            error_entry.detection_source = "sysfs"
                            errors.append(error_entry)
                    except (ValueError, IOError) as e:
                        # Skip this file if count cannot be read or converted
                        pass

        except (OSError, PermissionError) as e:
            # Log error if sysfs directory access fails
            LogManager().log(
                "MEMORY",
                LogManagerThread.Level.ERROR,
                f"Failed to access sysfs EDAC directory: {str(e)}",
            )

        return errors

    def _determine_thread_id(self, mc_id: str, dimm_label: str) -> str:
        """
        Determine thread ID by mapping memory errors to IMC execution threads.

        :param mc_id: Memory controller ID
        :param dimm_label: DIMM label
        :return: Thread identifier string
        """
        try:
            log_manager = LogManager()

            # Get list of current execution threads
            active_threads = (
                list(log_manager.thread_logs.keys())
                if hasattr(log_manager, "thread_logs")
                else []
            )

            if active_threads:
                mc_num = int(mc_id) if mc_id.isdigit() else 0
                thread_index = mc_num % len(active_threads)
                return active_threads[thread_index]

            if "MC#" in dimm_label:
                mc_match = re.search(r"MC#(\d+)", dimm_label)
                chan_match = re.search(r"Chan#(\d+)", dimm_label)

                if mc_match:
                    mc_num = int(mc_match.group(1))
                    chan_num = int(chan_match.group(1)) if chan_match else 0
                    return f"Thread-MC{mc_num}C{chan_num}"
            return f"Thread-MC{mc_id}"

        except (ValueError, TypeError, AttributeError) as e:
            # Return default thread name if thread mapping fails
            return "Thread-Unknown"

    def clear(self):
        """Clear errors - unused

        :return: None
        """
        return None
