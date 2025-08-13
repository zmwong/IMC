#!/usr/bin/python
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
import csv
import re

from scripts.libs.definitions.errors import XMLGeneratorStatus
from scripts.libs.definitions.imc import ParameterIdentifier, IMCParameter
from scripts.libs.definitions.imc import TOOL_NAME
from scripts.libs.definitions.imc import IMCOpcodeType, IMCTimeType
from scripts.libs.definitions.imc import IMCAlgorithm, IMCFlow
from scripts.libs.definitions.imc import IMCMemory
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)

# Initialize the logger using LoggerManager


def read_csv(path: str):
    csv_file = csv.DictReader(open(path), delimiter=",")
    return csv_file


def create_empty_dict(size=1):
    dict = {key: None for key in ParameterIdentifier}
    if size > 1:
        return [dict.copy() for _ in range(size)]
    else:
        return [dict]


def get_dict_value(test_case, dict_key, is_required, data_type):
    value = None
    try:
        value = test_case[dict_key]
    except KeyError:
        if is_required:
            status_code = XMLGeneratorStatus.REQUIRED_IDENTIFIER_DOES_NOT_EXIST
            raise ValueError(
                f"{status_code} Field: <{dict_key}> Error code: "
                + "({int(status_code)})"
            )

    if not value and is_required:
        status_code = XMLGeneratorStatus.REQUIRED_VALUE_NOT_FOUND
        raise ValueError(
            f"{status_code} Field: <{dict_key}> Error code: "
            + "({int(status_code)})"
        )
    elif value is not None and value != "":
        if is_incorrect_data_type(value, data_type):
            if is_required:
                status_code = XMLGeneratorStatus.INVALID_REQUIRED_VALUE
                raise ValueError(
                    f"{status_code} Field: <{dict_key}> Error code: "
                    + "({int(status_code)})"
                )

            else:
                status_code = XMLGeneratorStatus.INVALID_VALUE
                LoggerManager().log(
                    "SYS",
                    LoggerManagerThread.Level.INFO,
                    f"{status_code} Field: <{dict_key}> Error code: "
                    + "({int(status_code)})",
                )

    return value


def fill_imc_parameters(test_case, imc_parameters):
    parameters_result = set()
    execution_time = False
    for parameter in imc_parameters.copy():
        identifier = parameter.identifier
        value = get_dict_value(
            test_case,
            identifier,
            parameter.is_required,
            data_type=parameter.data_type,
        )

        if value:
            if identifier.name == "GLOBAL_TIME_TO_EXECUTE":
                time_value, unit = re.match(r"(\d+)([A-Z]+)", value).groups()
                time_node = IMCParameter(
                    identifier,
                    parameter.is_required,
                    parameter.data_type,
                    parameter.parameter_name,
                    time_value,
                )
                unit_node = IMCParameter(
                    ParameterIdentifier.GLOBAL_TIME_UNIT,
                    False,
                    str,
                    "time_unit",
                    unit,
                )
                parameters_result.add(time_node)
                parameters_result.add(unit_node)
                execution_time = True
            else:
                node = IMCParameter(
                    identifier,
                    parameter.is_required,
                    parameter.data_type,
                    parameter.parameter_name,
                    value,
                )
                parameters_result.add(node)

        elif parameter.inner_value != "" and parameter.inner_value is not None:
            # Include default
            node = IMCParameter(
                identifier,
                parameter.is_required,
                parameter.data_type,
                parameter.parameter_name,
                parameter.inner_value,
            )
            parameter.inner_value = str(parameter.inner_value)
            parameters_result.add(parameter)

    if execution_time:
        time_iterations = None
        for parameter in parameters_result:
            if parameter.identifier == ParameterIdentifier.GLOBAL_ITERATIONS:
                time_iterations = parameter
        if time_iterations:
            parameters_result.remove(time_iterations)

    return parameters_result


def is_valid_imc_time(time):

    if type(time) is str:
        if time.isdigit():
            time_number = time
            time_type = "SECONDS"
        match = re.fullmatch(r"(\d+)\D", time)

        if match:
            time_number = match.group(1)
            time_type = match.group(2)


def is_incorrect_data_type(data, data_type):
    # Check custom types
    if data_type not in [int, str, bool]:
        return not (isinstance(data, str))  # Replace with custom types

    else:
        try:
            if data_type is int:
                try:
                    int(data, 16)
                    return False
                except:
                    return not data.isdigit()

            elif data_type is bool:
                if data.capitalize() == "FALSE" or data.capitalize() == "TRUE":
                    return False
            elif type(data) is data_type:
                return False

            else:
                return True
        except:
            return True


def get_supported_opcode_names():
    opcode_list = [
        attr for attr in dir(IMCOpcodeType) if not attr.startswith("__")
    ]
    return opcode_list


def get_supported_time_types():
    time_list = [attr for attr in dir(IMCTimeType) if not attr.startswith("__")]
    return time_list


def get_enum_string_list(input_enum):
    enum_list = [attr for attr in dir(input_enum) if not attr.startswith("__")]
    return enum_list


def get_class_string_list(base_class):
    list = [x.NAME for x in base_class.Base.getTypes()]
    return list


def get_supported_flow_types():
    flow_list = [x.NAME for x in IMCFlow.Base.getFlows()]
    return flow_list


def get_supported_algorithm_types(pattern_type):
    algorithm_list = [
        x.NAME
        for x in IMCAlgorithm.Base.getTypesByPatternCompability(pattern_type)
    ]
    return algorithm_list


def get_supported_MEMORY_BLOCK_ALLOCATOR_TYPEs():
    block_list = [x.NAME for x in IMCMemory.MemoryBlock.getTypes()]
    return block_list


def get_supported_memory_group_types():
    group_list = [x.NAME for x in IMCMemory.MemoryGroup.getTypes()]
    return group_list
