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
This is the error manager base module which defines the base ErrorManager class.
"""

import logging
from typing import List, Set, Optional

from scripts.libs.errors.providers.factory import create_provider
from scripts.libs.definitions.errors import ErrorEntry, ErrorProvider
from scripts.libs.definitions.errors import (
    ErrorProviderNotFound,
    ErrorProviderNotSet,
)


_logger = logging.getLogger(__package__)


class ErrorManager:
    """
    Management interface for working with the providers and detecting errors
    """

    def __init__(
        self,
        collection_method: ErrorProvider = ErrorProvider.NoProvider,
        log_msg: Optional[bool] = True,
    ):
        """Constructor

        :param collection_method: Provider to use as the method of error
        collection
        """
        self._collection_method = collection_method
        self._start_errors = []
        self._end_errors = []
        self._provider = None

        try:
            self._provider = create_provider(collection_method)
            if self._provider:
                self._provider.init()

        except ErrorProviderNotFound as ex:
            if log_msg:
                _logger.error(ex)
            raise

    def mark_start(self):
        """
        Marks the start of the testing phase and retrieves a baseline list of
        errors on the system.

        :return: None
        """
        self._start_errors = self.get_errors()

    def mark_end(self):
        """
        Marks the end of the testing phase and retrieves the final list of
        errors on the system.

        :return: None
        """
        self._end_errors = self.get_errors()

    def get_marked_errors(self) -> Set[ErrorEntry]:
        """Generates a set of differences between the baseline errors and the
        final error list and returns them to the caller.

        :return: Set of error entries encountered during the testing.
        """
        return set(self._end_errors).difference(set(self._start_errors))

    def get_errors(self) -> List[ErrorEntry]:
        """Retrieves a list of error entries from the current error provider.

        :return: List of error entries
        """
        if not self._provider:
            return []

        try:
            return self._provider.get_errors()
        except ErrorProviderNotFound as ex:
            _logger.error(ex)

        return []

    def clear_errors(self):
        """Clears errors within the provider

        :return: None
        """
        if not self._provider:
            raise ErrorProviderNotSet("No provider configured.")

        self._provider.clear()

    def is_provider_set(self):
        """A public member to read the status of the provider.
        If the provider is None, ErrorProviderNotFound is raised.

        :return: None
        """
        if self._provider is None:
            raise ErrorProviderNotFound
        if hasattr(self._provider, "_fake_error"):  # LOD (imc_internal)
            raise ErrorProviderNotFound  # LOD (imc_internal)
