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
# pylint:

"""
    This is a support module for imc_runner which is used to determine if
    ftrace is available.
    If ftrace is available it will be configured to capture MCE.

    sudo / root privileges for sysfs is required for this to function correctly.

"""
import os
import re
import time
from typing import List, Optional

from scripts.libs.errors.providers.provider import BaseProvider
from scripts.libs.definitions.errors import ErrorEntry, ErrorProviderNotFound


class FtraceErrorEntry(ErrorEntry):
    """Representation of an error reported by ftrace"""

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

        return f"{self.event_type} error: {self._get_str()}"

    def __repr__(self) -> str:
        """Repr operator

        :return: str
        """
        return f"<FTraceErrorEntry(event_type={self.event_type}, \
            {self._get_str()})>"

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

    def _get_str(self):
        """Returns a dict of available objects used for human readability."""
        # pylint: disable=no-member
        ret_str = []
        if getattr(self, "socket", None):
            ret_str.append(f"socket={self.socket}")
        if getattr(self, "MCGc_s", None):
            ret_str.append(f"MCGc/s={self.MCGc_s}")
        if getattr(self, "mc_x", None):
            ret_str.append(f"{self.mc_x[0]}={self.mc_x[1]}")
        if getattr(self, "TSC", None):
            ret_str.append(f"tsc={self.TSC}")
        if getattr(self, "TIME", None):
            try:
                # convery the string value of time to int to use localtime
                format = "%m-%d-%Y %H:%M:%S"
                conversion = time.localtime(int(self.TIME))
                ret_str.append(f"at {time.strftime(format, conversion)}")
            except ValueError:
                pass

        return ", ".join(ret_str)

    def _parse_row_data(self, row_data: List[str]):
        """Processes the individual ftrace error entry items into our structure

        :param row_data: List of error entry items
        :return: None
        """
        if len(row_data) != 2:
            return
        self.raw = row_data
        self.event_type = row_data[0].replace(": ", "")
        s_event = row_data[1].replace(" ", "")  # remove empty space
        l_events = s_event.split(",")  # separate each item into a list
        for item in l_events:
            key, val = item.split(":", 1)
            key = key.replace("/", "_")  # convert to a valid key name
            if key == "SOCKET":
                self.socket = val
            elif re.match("MC[0-9]", key):
                self.mc_x = (key, val)
            else:
                self.__setattr__(key, val)


class FtraceProvider(BaseProvider):
    """Error provider for extracting errors from the ftrace log"""

    TRACING_PATH = "/sys/kernel/tracing/"
    AVAILABLE_EVENTS = TRACING_PATH + "available_events"
    SET_EVENT = TRACING_PATH + "set_event"
    TRACE_LOG = TRACING_PATH + "trace"
    EVENTS = ("mce:mce_record",)
    RESULT_ROW_ITEM_COUNT = 5
    RESULT_ROW_DELIMITER = ":"

    def __init__(self, events: Optional[list] = None):
        """Constructor"""
        if not events:
            events = FtraceProvider.EVENTS
        self.events = events
        super().__init__(path=None)
        self.prev_state = None

    def __del__(self):
        """Clean up the set trace on exit"""
        if self.prev_state is not None:
            self.set_trace(self.prev_state)  # set the trace state back

    def _self_test(self):
        """
        A test to verify that ftrace is available and the events required
        can be enabled.

        :return: None
        """
        available_events = []
        try:
            with open(self.AVAILABLE_EVENTS, "r", encoding="utf-8") as ft_fh:
                available_events = ft_fh.read().splitlines()
            if not list(set(self.events).intersection(available_events)):
                raise FileNotFoundError
            if not os.access(self.SET_EVENT, os.W_OK, follow_symlinks=True):
                raise PermissionError
        except FileNotFoundError as ex_err:
            raise ErrorProviderNotFound(
                f"{', '.join(self.EVENTS)} was not found in the available \
                    ftrace events in {self.AVAILABLE_EVENTS}."
            ) from ex_err
        except PermissionError as ex_err:
            raise ErrorProviderNotFound(
                f"The current user does not have permission to access \
                    {self.SET_EVENT}."
            ) from ex_err

    def init(self):
        """
        Provider initialization - verifies that ftrace can be enabled and has
        the events reqired.

        :return: None
        """
        self._self_test()
        self.prev_state = self.is_set()
        self.set_trace()

    def _get_alt_paths(self) -> list:
        """Find the secondary path to the event status."""
        alt_paths = []
        events_path = os.path.join(self.TRACING_PATH, "events")
        for event in self.EVENTS:
            root, item = event.split(":")
            alt_path = os.path.join(events_path, root, item)
            if os.path.exists(alt_path) and alt_path != events_path:
                alt_paths.append(alt_path)
        return alt_paths

    def is_set(self) -> bool:
        """Returns true if the events are set.
        :return: True if set, False otherwise
        """
        with open(self.SET_EVENT, "r", encoding="utf-8") as ft_fh:
            set_events = ft_fh.read().splitlines()
        return any(set(self.events).intersection(set_events))

    def set_trace(self, enabled: bool = True) -> bool:
        """Enables ftrace for selects events."""
        try:
            self._self_test()
            # Must open as read+ as not to remove any other events configured
            # and cannot be opended in append mode
            with open(self.SET_EVENT, "r+", encoding="utf-8") as ft_fh:
                for event in self.EVENTS:
                    if not enabled:
                        # The ftrace events are disabled by '!<event>'
                        event = "!" + event
                    ft_fh.write(event)
                    ft_fh.flush()
            # check that it's set
            return self.is_set()
        except (ErrorProviderNotFound, FileNotFoundError, PermissionError):
            return False

    def get_errors(self) -> List[FtraceErrorEntry]:
        """Retrieve a list of errors from the provider

        :return: List of FtraceErrorEntry
        """
        self._self_test()
        errors = []

        with open(self.TRACE_LOG, "r", encoding="utf-8") as ft_fh:
            events = ft_fh.read().splitlines()
        # convert the EVENTS to match the ftrace log labels
        event_tags = set(x.split(":")[-1:][0] for x in self.EVENTS)

        # Only parse supported events from self.EVENTS/event_tags
        for event in [x for x in events if any(y in x for y in event_tags)]:
            # parse the mce_record 'event_tag' data
            for event_tag in event_tags:
                supported_events = event.partition(f"{event_tag}: ")[-2:]
                errors.append(FtraceErrorEntry(supported_events))
        return errors

    def clear(self):
        """Clear errors - unused

        :return: None
        """
        return None

    def _execute(self) -> List[str]:
        """Creates a thread to watch the ftrace log

        :return: List of strings
        """
        results = []

        return results
