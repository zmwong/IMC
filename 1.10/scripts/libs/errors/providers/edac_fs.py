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

"""
This module supports edac error collection by reading the edac_fs from
/sys/devices/system/edac.
"""

import os
import re
from typing import List, Optional

from scripts.libs.definitions.errors import ErrorType, ErrorProviderNotFound
from scripts.libs.errors.providers.edac import EDACProvider, EDACErrorEntry


def _read_file(file_path) -> str:
    """
    This method checks if the file (file_path) exists.
    If so, returns the content. If the file doesn't exist, it returns None
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file_handler:
            return file_handler.read().strip()
    return None


def _update_sub_comp(
    sub_comp_map: dict, errors: dict, dimm_label: str, error_type: str
):
    """
    This method is used in the unlikely case where the csrowX structure doesn't
    have the chX_ue_count, or the chX_ce_count files. In such case, errors are
    reported per mcX/csrowY, instead of csrowX/chY. That means, total ce or ue
    errors per csrow.
    Receives:
    sub_comp_map: a dictionary that maps mcX_csrowY, csrowY sub-directory path,
        and the dimm_label that is missing the ce or ue.
    errors: the dictionary to be returned by main(). This method will add
        information to this dictionary.
    dimm_label: the dimm_label that is missing the ce or ue.
    error_type: the error type that is missing (ce or ue).
    """
    for sub_component in sub_comp_map.keys():
        if sub_comp_map[sub_component]["dimm_label"] == dimm_label:
            csr_dir_path = os.path.join(
                sub_comp_map[sub_component]["path"], error_type
            )
            error_count = _read_file(csr_dir_path)
            if error_count and "csrow" in csr_dir_path:
                errors[sub_component] = {}
                errors[sub_component][error_type] = int(error_count)


class EDACFsErrorEntry(EDACErrorEntry):
    """ "
    This class supports each of the error entries for the error provider.
    """

    # pylint: disable=too-many-instance-attributes

    def __repr__(self) -> str:
        """Repr operator

        :return: str
        """
        return f"<EDACFsErrorEntry(error_type={str(self.error_type)}, \
            count={self.count}, socket={self.socket}, mc={self.mc}, \
            channel={self.channel}, slot={self.slot})>"

    def _parse_row_data(self, row_data: List[str]):
        """Processes the individual error entry items into our structure

        :param row_data: List of error entry items
        :return: None
        """
        dimm_label, error_type, error_count = row_data

        self.dimm_label = dimm_label
        self.error_type = EDACErrorEntry.ERROR_TYPES.get(
            error_type, ErrorType.Unknown
        )
        self.count = error_count

        self.raw = EDACProvider.RESULT_ROW_DELIMITER.join(row_data)
        self._update_dimm_details(dimm_label)


class EDACFsProvider(EDACProvider):
    """ " This class is the primary class consumed by the error factory."""

    # mc directory in edac file system
    EDAC_MC_PATH = "/sys/devices/system/edac/mc"

    def __init__(self, path: Optional[str] = None):
        super().__init__(path=path)

    def _self_test(self):
        rematch = re.compile("mc[0-9]+")
        if not os.path.exists(EDACFsProvider.EDAC_MC_PATH) or not any(
            filter(rematch.match, os.listdir(EDACFsProvider.EDAC_MC_PATH))
        ):
            raise ErrorProviderNotFound(
                f"No memory controllers were found in path: \
                    {EDACFsProvider.EDAC_MC_PATH}; please make sure edac is \
                    properly configured."
            )

    def init(self):
        # Verifies that at least one mc exists and that edacfs is working.
        self._self_test()

    def get_errors(self) -> List[EDACErrorEntry]:
        """Retrieve a list of errors from the provider

        :return: List of EDACErrorEntry
        """
        self._self_test()

        errors = []

        results_dict = self._execute()
        labels = sorted(results_dict.keys())
        for dimm_info in labels:
            if results_dict[dimm_info]["ce_count"] > 0:
                row_data = [
                    dimm_info,
                    ErrorType.CE.name,
                    str(results_dict[dimm_info]["ce_count"]),
                ]
                errors.append(EDACFsErrorEntry(row_data))
            if results_dict[dimm_info]["ue_count"] > 0:
                row_data = [
                    dimm_info,
                    ErrorType.UE.name,
                    str(results_dict[dimm_info]["ue_count"]),
                ]
                errors.append(EDACFsErrorEntry(row_data))
        return errors

    def _execute(self) -> List[str]:
        # pylint: disable=too-many-locals,too-many-nested-blocks
        # too-many-branches
        # directory containing files of interest
        end_dir_regex = "((dimm[0-9])|(csrow[0-9]))"
        # file of interest (dimm label)
        dimm_label_file_regex = "^(ch[0-9]_)?dimm_label"
        error_dict = {}  # dictionary to be populated with errors
        # dictionary to be used only in the unlikely legacy case where the
        # csrowX structure is missing the ce_count or ue_count files
        mc_subcomponent_mapping = {}

        for mc_subdir, _, end_files in os.walk(EDACFsProvider.EDAC_MC_PATH):
            if re.search(r".+\/" + end_dir_regex + "$", mc_subdir):
                for end_files_i in end_files:
                    if re.search(dimm_label_file_regex, end_files_i):
                        mc_subcomponent_tag = (
                            mc_subdir.split("/")[-2]
                            + "_"
                            + mc_subdir.split("/")[-1]
                        )
                        mc_subcomponent_mapping[mc_subcomponent_tag] = {}
                        mc_subcomponent_mapping[mc_subcomponent_tag][
                            "path"
                        ] = mc_subdir

                        if "ch" in end_files_i:  # Legacy
                            ce_tag = f"ch{end_files_i[2]}_ce_count"
                            ue_tag = f"ch{end_files_i[2]}_ue_count"
                        else:
                            ce_tag = "dimm_ce_count"
                            ue_tag = "dimm_ue_count"
                        dimm_label_file = os.path.join(mc_subdir, end_files_i)
                        dimm_label = _read_file(dimm_label_file).replace(
                            "\n", ""
                        )
                        mc_subcomponent_mapping[mc_subcomponent_tag][
                            "dimm_label"
                        ] = dimm_label
                        if dimm_label not in error_dict:
                            # Create new dict the first time the tag is found
                            error_dict[dimm_label] = {}
                        # Get CE errors
                        ce_file_path = os.path.join(mc_subdir, ce_tag)
                        if os.path.exists(ce_file_path):
                            ce_val = _read_file(ce_file_path)
                            ce_count = (
                                int(ce_val)
                                if ce_val and ce_val.isdigit()
                                else -1
                            )
                            if error_dict[dimm_label].get("ce_count", -1) == -1:
                                error_dict[dimm_label]["ce_count"] = ce_count
                        elif "ce_count" not in error_dict[dimm_label].keys():
                            error_dict[dimm_label]["ce_count"] = -1
                        # Now UE errors
                        ue_file_path = os.path.join(mc_subdir, ue_tag)
                        if os.path.exists(ue_file_path):
                            ue_val = _read_file(ue_file_path)
                            ue_count = (
                                int(ue_val)
                                if ue_val and ue_val.isdigit()
                                else -1
                            )
                            if error_dict[dimm_label].get("ue_count", -1) == -1:
                                error_dict[dimm_label]["ue_count"] = ue_count
                        elif "ue_count" not in error_dict[dimm_label].keys():
                            error_dict[dimm_label]["ue_count"] = -1
        # Handling the case where ue_count or ce_count were not found by
        # dimm_label. Errors will be reported with csrowX granularity,
        # instead of dimm granularity.
        # Applies only for legacy case
        for each_dimm_label in list(error_dict.keys()):
            if error_dict[each_dimm_label]["ce_count"] == -1:
                _update_sub_comp(
                    mc_subcomponent_mapping,
                    error_dict,
                    each_dimm_label,
                    "ce_count",
                )
            if error_dict[each_dimm_label]["ue_count"] == -1:
                _update_sub_comp(
                    mc_subcomponent_mapping,
                    error_dict,
                    each_dimm_label,
                    "ue_count",
                )
        return error_dict
