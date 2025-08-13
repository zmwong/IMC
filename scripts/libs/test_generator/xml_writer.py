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

import os
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom

from ..definitions.imc import ParameterName, ParameterIdentifier
from ..definitions.imc import IMCParameter, TOOL_NAME
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)


from scripts.libs.definitions.errors import XMLGeneratorStatus


class XMLTest:
    """Defines how a test of type XML should be written using xml.etree
    library."""

    def __init__(self) -> None:
        self._xml_root = ET.Element(ParameterName.ROOT)
        self._xml_tree = ET.ElementTree(self._xml_root)
        self._imc_control_block = ET.SubElement(
            self._xml_root, ParameterName.IMC_CONTROL_BLOCK
        )

    def set_imc_control_parameters(self, imc_control_parameters):
        status_code = add_nodes_to_xml_block(
            imc_control_parameters, self._imc_control_block
        )
        return status_code

    def set_flow_parameters(self, flow_parameters, flow_name):
        self._flow_block = ET.SubElement(self._xml_root, flow_name)
        self._handle_list_parameters(self._flow_block, flow_parameters)
        status_code = add_nodes_to_xml_block(flow_parameters, self._flow_block)
        return status_code

    def set_algorithm_parameters(self, algorithm_parameters):
        for algorithm in algorithm_parameters:
            (algorithm_name, _, algorithm_parameters) = algorithm

            algorithm_block = ET.SubElement(self._xml_root, algorithm_name)
            self._handle_list_parameters(algorithm_block, algorithm_parameters)

            status_code = add_nodes_to_xml_block(
                algorithm_parameters, algorithm_block
            )
        return status_code

    def _handle_list_parameters(self, target_xml_block, parameters):
        parameter_list = next(
            (
                parameter
                for parameter in parameters
                if isinstance(parameter.data_type, tuple)
            ),
            None,
        )
        if parameter_list is not None:
            # conver to type list separating by ',' or '[,,],[,]'
            if (
                "[" in parameter_list.inner_value
                or "]" in parameter_list.inner_value
            ):
                serialized_list = re.findall(
                    r"\[.*?\]", parameter_list.inner_value
                )
            else:
                serialized_list = parameter_list.inner_value.split(",")

            # clean up
            serialized_list = [x for x in serialized_list if x]
            serialized_list = [x.strip("[]") for x in serialized_list if x]
            for element in serialized_list:
                add_node_to_xml_block(
                    target_xml_block, parameter_list.identifier, element
                )
            parameters.remove(parameter_list)

    def set_memory_parameters(self, memory_parameters):
        # Write memory parameters
        (memory_block_parameters, memory_group_parameters) = memory_parameters

        # If memory block parameter is defined
        if memory_block_parameters:
            (parameters, blocks_amount) = memory_block_parameters
            # Create List to include save parameters for special cases
            additional_parameters = list()
            # Ex. having a list of target_paths

            # Check if target_path is defined
            if ParameterIdentifier.MEMORY_BLOCK_TARGET_PATH in [
                param.identifier for param in parameters
            ]:
                # Retrieve target_path param
                for parameter in parameters.copy():
                    if (
                        parameter.identifier
                        == ParameterIdentifier.MEMORY_BLOCK_TARGET_PATH
                    ):
                        target_path_parameter = parameter
                        target_path_list = target_path_parameter.inner_value
                        break

                # Convert target_path, comma delimited paths to a list
                try:
                    target_path = target_path_list.split(",")
                    target_path_list = list()
                    for path in target_path:
                        target_path_list.append(
                            IMCParameter(
                                ParameterIdentifier.MEMORY_BLOCK_TARGET_PATH,
                                False,
                                str,
                                ParameterName.TARGET_PATH,
                                inner_value=path,
                            )
                        )
                    additional_parameters.append(target_path_list)
                    # Delete parameter

                    parameters.remove(target_path_parameter)

                except Exception as e:
                    print(e)

            for block_count in range(blocks_amount):
                block_id = ParameterName.MEMORY_BLOCK_ID + str(block_count)

                memory_xml_block = ET.SubElement(self._xml_root, block_id)

                status_code = add_nodes_to_xml_block(
                    parameters, memory_xml_block
                )

                # Add edge case additional parameters
                for additional_parameter in [
                    additional_param
                    for additional_param in additional_parameters
                    if len(additional_param) != 0
                ]:

                    if isinstance(additional_parameter, list):
                        new_parameter = additional_parameter.pop()
                    else:
                        new_parameter = additional_parameter

                    identifier = new_parameter.identifier
                    inner_value = new_parameter.inner_value

                    add_node_to_xml_block(
                        memory_xml_block, identifier, inner_value
                    )

                # Add memory block node to flow block
                add_node_to_xml_block(
                    self._flow_block, ParameterName.MEMORY_BLOCK, block_id
                )

        if memory_group_parameters:
            memory_block_group_xml_block = ET.SubElement(
                self._xml_root, ParameterName.MEMORY_BLOCK_GROUP_ID
            )

            status_code = add_nodes_to_xml_block(
                memory_group_parameters, memory_block_group_xml_block
            )

            # Add memory group node to flow block
            add_node_to_xml_block(
                self._flow_block,
                ParameterName.MEMORY_BLOCK_GROUP,
                ParameterName.MEMORY_BLOCK_GROUP_ID,
            )
        return status_code

    def write_file(self, path, file_name):
        write_xml_file(self._xml_tree, path, file_name)


def add_node_to_xml_block(xml_block, node_id, node_inner_value):
    """Helper function that adds a single xml node, an IMC parameter,
    to a XML block.
    :param xml_block: the xml_block where the node will be added.
    :param node_id: the id of the node. Ex. <iterations>
    :param node_inner_value: the inner value of the node.
    Ex. <iterations>VALUE</iterations>
    """
    new_node = ET.SubElement(xml_block, node_id)
    new_node.text = node_inner_value


def add_nodes_to_xml_block(nodes_to_add, xml_block):
    """Helper function that adds multiple xml nodes, IMC parameters,
    to a XML block.
    :param nodes_to_add: set of params to be added.
    :param xml_block: the xml_block where the nodes will be added.
    """

    status_code = XMLGeneratorStatus.OK

    for xml_node in nodes_to_add:
        xml_inner_value = xml_node.inner_value
        parameter_node = ET.SubElement(xml_block, xml_node.parameter_name)
        parameter_node.text = xml_inner_value

    return status_code


def write_xml_file(xml_tree, write_path, file_name):
    """Write the xml test, given the path, the xml data and file name.
    :param xml_tree: tree that contains the whole xml test.
    :param write_path: target path of the test.
    :param file_name: name of the test.
    """
    if not os.path.exists(write_path):  # show error if path is not accesible.
        try:
            os.makedirs(write_path)
        except PermissionError:
            status_code = XMLGeneratorStatus.INVALID_PATH
            raise ValueError(
                f"{status_code} {write_path} Error code: ({int(status_code)})"
            )

    index = ""
    while True:  # While loop to verify if the file name already exists,
        # and iterate a number
        # appended to the file name until the file name is different.
        file_test = os.path.join(write_path, (file_name + index + ".xml"))
        if not os.path.isfile(file_test):
            break
        else:  # File with name already exists
            if index:
                # Append 1 to number in brackets
                index = "(" + str(int(index[1:-1]) + 1) + ")"
            else:
                index = "(1)"
            LoggerManager().log(
                "SYS",
                LoggerManagerThread.Level.WARNING,
                f"File {file_test} already exists, appending number {index}.",
            )

    file_name = file_name + index + ".xml"
    xml_string = ET.tostring(xml_tree._root, encoding="utf-8")
    dom = xml.dom.minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="\t")
    with open(os.path.join(write_path, file_name), "wb") as file:
        file.write(pretty_xml.encode("utf-8"))
