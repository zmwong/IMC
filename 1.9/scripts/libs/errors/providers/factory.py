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
""" This module supports the error factory. """

from typing import Optional, TypeVar

from scripts.libs.errors.providers.edac import EDACProvider
from scripts.libs.errors.providers.edac_fs import EDACFsProvider
from scripts.libs.errors.providers.ftrace import FtraceProvider
from scripts.libs.errors.providers.provider import BaseProvider
from scripts.libs.definitions.errors import ErrorProvider
from scripts.libs.definitions.errors import DEV_MODE  # LOD (imc_internal)


PROVIDER_MAP = {
    ErrorProvider.NoProvider: None,
    ErrorProvider.EDAC: EDACProvider,
    ErrorProvider.EDACFS: EDACFsProvider,
    ErrorProvider.Ftrace: FtraceProvider,
}

# LOD (imc_internal)
if DEV_MODE:
    from scripts.libs.errors.providers.edac import FakeEDACProvider

    PROVIDER_MAP[ErrorProvider.FakeEDAC] = FakeEDACProvider
# LOD END


def create_provider(error_provider: ErrorProvider) -> Optional[BaseProvider]:
    """Constructs a provider based on the identifier provided

    :param error_provider: Error provider enum
    :return: instance of error provider
    """
    provider_cls: Optional[TypeVar] = PROVIDER_MAP.get(error_provider)
    if not provider_cls:
        return None

    obj = provider_cls()

    return obj
