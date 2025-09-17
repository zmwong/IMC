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

import os
import csv
from datetime import datetime

from .xml_writer import XMLTest
from scripts.libs.test_generator import generator_parser
from scripts.libs.definitions.errors import XMLGeneratorStatus
from scripts.libs.definitions.imc import IMCAlgorithm
from scripts.libs.definitions.imc import IMCFlow
from scripts.libs.definitions.imc import IMCMemory
from scripts.libs.definitions.imc import IMCControl
from scripts.libs.definitions.imc import PatternType
from scripts.libs.definitions.imc import ParameterIdentifier, TOOL_NAME
from scripts.libs.definitions.imc import MemoryType
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)


OUTPUT_FOLDER = "generated_tests_" + str(
    datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
)
current_dir = os.path.abspath(os.path.dirname(__file__))
dirs = current_dir.split(os.sep)
scripts_index = dirs.index("scripts")
resources_dir = os.sep.join(dirs[:scripts_index] + ["resources"])

WRITE_PATH = os.path.join(resources_dir)


def read_flow_parameters(test_case):
    """Read flow-related parameters from the dictionary, and save the results
    inside an IMCParameter set.
    :param test_case: test_case dictionary.
    :return: tuple with flow_parameters set, flow name, and pattern_type."""
    flow_name = generator_parser.get_dict_value(
        test_case,
        ParameterIdentifier.FLOW_TYPE,
        is_required=True,
        data_type=str,
    )

    specialized_flow = IMCFlow.Base.getSubclassByName(flow_name)

    if not specialized_flow:
        status_code = XMLGeneratorStatus.REQUIRED_VALUE_NOT_DEFINED
        raise ValueError(
            f"{status_code} Field: {flow_name} "
            f"Error code: ({int(status_code)})"
        )

    specialized_flow = specialized_flow()

    # Validate if pattern type matches what the dict has
    pattern_type = specialized_flow.type

    try:
        address_algorithm = generator_parser.get_dict_value(
            test_case,
            ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
            is_required=True,
            data_type=str,
        )
    except (ValueError, TypeError):
        address_algorithm = None

    try:
        data_algorithm = generator_parser.get_dict_value(
            test_case,
            ParameterIdentifier.DATA_ALGORITHM_TYPE,
            is_required=True,
            data_type=str,
        )
    except (ValueError, TypeError):
        data_algorithm = None

    if not address_algorithm and not data_algorithm:
        status_code = XMLGeneratorStatus.INCOMPATIBLE_CONFIGURATION
        raise ValueError(
            f"{status_code} Field: Address and data algorithms. "
            f"Error code: ({int(status_code)})"
        )

    elif pattern_type == PatternType.ADDRESS and not address_algorithm:
        status_code = XMLGeneratorStatus.INCOMPATIBLE_CONFIGURATION
        raise ValueError(
            f"{status_code} Field: Address algorithm. "
            f" Error code: ({int(status_code)})"
        )

    elif pattern_type == PatternType.DATA and not data_algorithm:
        status_code = XMLGeneratorStatus.INCOMPATIBLE_CONFIGURATION
        raise ValueError(
            f"{status_code} Field: Data algorithm. "
            f"Error code: ({int(status_code)})"
        )

    elif (
        not address_algorithm
        and not data_algorithm
        and pattern_type != PatternType.DATA_AND_ADDRESS
    ):
        status_code = XMLGeneratorStatus.INCOMPATIBLE_CONFIGURATION
        raise ValueError(f"{status_code} Error code: ({int(status_code)})")

    flow_parameters = generator_parser.fill_imc_parameters(
        test_case, specialized_flow.PARAMETERS
    )

    return flow_parameters, flow_name, pattern_type


def read_algorithm_parameters(test_case, pattern_type):
    """Read algorithm-related parameters from the dictionary, and save the
    results inside a IMCParameter set.
    :param test_case: test_case dictionary.
    :param pattern_type: pattern type previously retrieved from flow.
    :return: algorithm_parameters set."""

    # Get algorithm name
    if pattern_type == PatternType.DATA:

        algorithm_name = generator_parser.get_dict_value(
            test_case,
            ParameterIdentifier.DATA_ALGORITHM_TYPE,
            is_required=True,
            data_type=str,
        )

        algorithm_parameters_searcher = [(algorithm_name, pattern_type, set())]

    elif pattern_type == PatternType.ADDRESS:

        algorithm_name = generator_parser.get_dict_value(
            test_case,
            ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
            is_required=True,
            data_type=str,
        )

        algorithm_parameters_searcher = [(algorithm_name, pattern_type, set())]

    elif pattern_type == PatternType.DATA_AND_ADDRESS:

        data_algorithm_name = generator_parser.get_dict_value(
            test_case,
            ParameterIdentifier.DATA_ALGORITHM_TYPE,
            is_required=True,
            data_type=str,
        )

        address_algorithm_name = generator_parser.get_dict_value(
            test_case,
            ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
            is_required=True,
            data_type=str,
        )

        data_parameter = (data_algorithm_name, PatternType.DATA, set())

        address_parameter = (address_algorithm_name, PatternType.ADDRESS, set())

        algorithm_parameters_searcher = [data_parameter, address_parameter]

    # Get algorithms data
    algorithms_parameters = []

    for algorithm_type in algorithm_parameters_searcher:
        (algorithm_name, algorithm_pattern_type, algorithm_parameters) = (
            algorithm_type
        )

        specialized_algorithm = IMCAlgorithm.Base.getSubclassByName(
            algorithm_name
        )

        if not specialized_algorithm:
            status_code = XMLGeneratorStatus.REQUIRED_VALUE_NOT_FOUND
            raise ValueError(
                f"{status_code} Algorithm {algorithm_name} is not valid. "
                f"Error code: ({int(status_code)})"
            )

        specialized_algorithm = specialized_algorithm(
            type=algorithm_pattern_type
        )

        # Check if algorithm is compatible with the flow's pattern.
        if (
            specialized_algorithm.pattern_compability
            != PatternType.DATA_AND_ADDRESS
            and specialized_algorithm.pattern_compability
            != algorithm_pattern_type
        ):

            status_code = XMLGeneratorStatus.INCOMPATIBLE_CONFIGURATION
            raise ValueError(
                f"""{status_code} Algorithm {algorithm_name} \
is not compatible for pattern {algorithm_pattern_type.name}. \
Error code: ({int(status_code)})"""
            )

        algorithm_parameters = generator_parser.fill_imc_parameters(
            test_case, specialized_algorithm.PARAMETERS
        )

        algorithms_parameters.append(
            (algorithm_name, algorithm_pattern_type, algorithm_parameters)
        )

    return algorithms_parameters


def read_memory_parameters(test_case):
    """Read memory-related parameters from the dictionary, and save the
    results inside a IMCParameter set.
    :param test_case: test_case dictionary.
    :return: memory_parameters set. Can be a tuple if both memory group and
    block parameters have been defined."""
    memory_group_parameters = None
    memory_block_parameters = None
    # Get memory group parameters
    memory_group_allocator = generator_parser.get_dict_value(
        test_case,
        ParameterIdentifier.MEMORY_GROUP_BLOCK_TYPE,
        is_required=False,
        data_type=str,
    )

    specialized_memory_group = IMCMemory.Base.getSubclassByName(
        memory_group_allocator
    )

    if specialized_memory_group:
        specialized_memory_group = specialized_memory_group(MemoryType.GROUP)

        memory_group_parameters = generator_parser.fill_imc_parameters(
            test_case, specialized_memory_group.PARAMETERS
        )

    # Get memory block parameters
    memory_block_allocator = generator_parser.get_dict_value(
        test_case,
        ParameterIdentifier.MEMORY_BLOCK_ALLOCATOR_TYPE,
        is_required=False,
        data_type=str,
    )

    specialized_memory_block = IMCMemory.Base.getSubclassByName(
        memory_block_allocator
    )

    if specialized_memory_block:
        specialized_memory_block = specialized_memory_block(MemoryType.BLOCK)

        memory_block_parameters = generator_parser.fill_imc_parameters(
            test_case, specialized_memory_block.PARAMETERS
        )
        memory_block_amount = generator_parser.get_dict_value(
            test_case,
            ParameterIdentifier.MEMORY_BLOCK_AMOUNT,
            is_required=False,
            data_type=int,
        )
        try:
            memory_block_amount = int(memory_block_amount)
        except BaseException:
            status_code = XMLGeneratorStatus.INVALID_REQUIRED_VALUE
            raise ValueError(
                f"{status_code} Field: <Memory block amount> "
                f" Error code: ({int(status_code)})"
            )

        memory_block_parameters = (memory_block_parameters, memory_block_amount)

    # Verify memory block and memory group status
    if memory_group_parameters and memory_block_parameters:
        memory_parameters = (memory_block_parameters, memory_group_parameters)

    elif not memory_group_parameters and memory_block_parameters:
        memory_parameters = (memory_block_parameters, ())

    elif memory_group_parameters and not memory_block_parameters:
        memory_parameters = ((), memory_group_parameters)

    else:
        status_code = XMLGeneratorStatus.INVALID_REQUIRED_VALUE
        raise ValueError(
            f"{status_code} Memory block and memory group configuration is "
            f"not valid. Error code: ({int(status_code)})"
        )

    return memory_parameters


def read_control_parameters(test_case):
    """Read control-related parameters from the dictionary, and save the
    results inside a IMCParameter set.
    :param test_case: test_case dictionary.
    :return: imc_control_parameters set."""
    imc_control_parameters = generator_parser.fill_imc_parameters(
        test_case, IMCControl().PARAMETERS
    )
    return imc_control_parameters


def generate_tests(
    data_source, continue_on_fail=True, write_test=True, write_path=WRITE_PATH
):
    """Generate tests from dictionary.
    :param data_source: dictionary with the test information to be generated.
    Can be a list if multiple tests.
    :param continue_on_fail: boolean. Incase with multiple tests, set if test
    generation should continue if one fails.
    :param write_test: boolean. Set if tests should be generated.
    :param write_path: path where the tests should be written.
    """
    if not isinstance(data_source, list) and not isinstance(
        data_source, csv.DictReader
    ):
        data_source = [data_source]

    for i, test_case in enumerate(data_source):
        # READING PHASE
        try:
            # Read IMC control parameters
            imc_control_parameters = read_control_parameters(test_case)

            # Read flow parameters

            (flow_parameters, flow_name, pattern_type) = read_flow_parameters(
                test_case
            )

            # Read algorithm parameters
            algorithms_parameters = read_algorithm_parameters(
                test_case, pattern_type
            )

            # Read memory parameters
            memory_parameters = read_memory_parameters(test_case)

            # Check if file name exists, if not create custom file name
            file_name = generator_parser.get_dict_value(
                test_case,
                ParameterIdentifier.FILE_NAME,
                is_required=False,
                data_type=str,
            )
            if not file_name:
                file_name = f"{flow_name}_" + (
                    "_".join(
                        map(
                            lambda algorithm: f"{algorithm[1].name}_{algorithm[0]}",
                            algorithms_parameters,
                        )
                    )
                )

            # XML WRITING PHASE
            if write_test:
                xml_test = XMLTest()

                xml_test.set_imc_control_parameters(imc_control_parameters)

                xml_test.set_flow_parameters(flow_parameters, flow_name)

                xml_test.set_algorithm_parameters(algorithms_parameters)

                xml_test.set_memory_parameters(memory_parameters)

                # Write XML
                xml_test.write_file(write_path, file_name)

        except (ValueError, TypeError) as ex_err:
            LoggerManager().log(
                "SYS",
                LoggerManagerThread.Level.ERROR,
                f"Test {i}. {ex_err}",
            )
            if continue_on_fail:
                continue
            else:
                return -1

    return 0
