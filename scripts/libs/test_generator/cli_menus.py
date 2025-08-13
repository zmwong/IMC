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

from __future__ import annotations
from threading import Lock
import enum
import inspect
from itertools import tee
import sys
from abc import ABC, abstractmethod

from scripts.libs.definitions.imc import IMCControl
from scripts.libs.definitions.imc import IMCMemory
from scripts.libs.definitions.imc import IMCFlow
from scripts.libs.definitions.imc import IMCAlgorithm
from scripts.libs.definitions.imc import IMCTimeType
from scripts.libs.definitions.imc import IMCParameter
from scripts.libs.definitions.imc import ParameterIdentifier
from scripts.libs.definitions.imc import PatternType
from scripts.libs.definitions.imc import ParameterName
from scripts.libs.definitions.imc import ListTypes
from scripts.libs.definitions.imc import MemoryType
from scripts.libs.test_generator.generator_parser import create_empty_dict
from scripts.libs.test_generator.generator_parser import is_incorrect_data_type
from scripts.libs.test_generator.generator_parser import get_enum_string_list
from scripts.libs.test_generator.generator_parser import get_class_string_list
from scripts.libs.test_generator.generator_parser import (
    get_supported_algorithm_types,
)


def _parse_user_input(user_input, type):
    """
    Gets the user input data, makes sure its the appropiate data type input,
    handles a program stop if user chooses 0, and verifies if menu is complete
    before continuing
    """
    if user_input == "0" or user_input == 0:  # stop app
        sys.exit("No test cases were generated.")

    elif user_input == "":  # Handle next menu.
        if MenuContext().get_current_menu().menu_is_complete():
            MenuContext().get_current_menu().next_menu()
        else:
            input("Complete the current menu first.")
        return (False, None)

    else:
        if is_incorrect_data_type(user_input, type):
            return (False, None)
        else:
            return (True, type(user_input))


def _data_requires_additional_menu(data_type):
    """
    Verifies if data to be asked needs an additional menu state or options.
    """
    return data_type not in [int, str]


def _handle_specialized_data(selected_option):
    """
    For data that needs additional questions or input, provides the required
    menus.
    """
    data_type = selected_option.data_type
    if data_type == bool:
        print(
            f"""
        Choose {selected_option.parameter_name} boolean value:
        1. True
        2. False
        """
        )
        user_input = str(input("Choose value: "))
        (is_valid, sanitized_input) = _parse_user_input(user_input, int)
        if is_valid:
            if sanitized_input == 1:
                return "true"
            elif sanitized_input == 2:
                return "false"
        else:
            _handle_specialized_data(selected_option)

    elif isinstance(data_type, tuple):
        if data_type[0] == list:
            msg = "How many elements do you want in the list?: "
            user_input = str(input(msg))
            (is_valid, sanitized_input) = _parse_user_input(user_input, int)
            if is_valid:
                list_string: str = ""
                for number in range(sanitized_input):
                    user_input = str(input(f"Input element {number+1}: "))
                    if data_type[1] == ListTypes.March_Element:
                        list_string += "[" + user_input + "],"
                    elif data_type[1 == ListTypes.Pattern_List]:
                        list_string += user_input + ","
                return list_string
        else:
            _handle_specialized_data(selected_option)

    elif data_type == IMCTimeType:
        MenuContext()._change_menu_to(
            TimeSelectionMenu(
                MenuContext().get_current_menu(), selected_option.identifier
            )
        )
    else:
        MenuContext()._change_menu_to(
            ListSelectionMenu(
                MenuContext().get_current_menu(),
                data_type,
                selected_option.identifier,
            )
        )


class MenuStrings(enum.Enum):
    """Instructions or text shown inside each menu.
    Declared as a tuple: the menu title and the instruction text."""

    FlowQuantity = (
        "Flow quantity selection 1/6",
        "How many flows do you want to generate?",
    )
    FlowTypeSelection = "Flow type selection 2/6", "Choose desired flow:"
    GlobalExecution = (
        "Global execution configuration 3/6",
        "Choose a number to modify its value:",
    )
    IMCTimeSelection = "Execution time", "Select execution time:"
    FlowParameters = (
        "Flow parameter options 4/6",
        "Choose parameters for flow {0}.",
    )
    AlgorithmParameters = (
        "Algorithm parameter options 5/6",
        "Choose parameters for {0} algorithm.",
    )
    IMCTimeOpcodeSelection = "Opcode type", "Choose opcode type:"
    AlgorithmTypeSelection = (
        "Algorithm type selection",
        "Choose desired algorithm:",
    )
    MemoryParameters = (
        "Memory configuration 6/6",
        "Choose parameters for memory {0}",
    )
    MemoryType = (
        "Memory configuration 6/6",
        """

Memory blocks created individually: <{0}>
Memory blocks created from group: <{1}>

Choose type of memory: """,
    )

    @staticmethod
    def _format_description(enum_member, replacement_string):
        """For menus with dynamic text, which are marked with {n}.
        :param enum_member: enum to add dynamic text
        :param replacement_string: string to add to text.
                                A list if multiple strings.
        :return: Copy of the enum with the text replaced.
        """

        if isinstance(replacement_string, list):
            formatted_value = (
                enum_member.value[0],
                enum_member.value[1].format(*replacement_string),
            )

        else:
            formatted_value = (
                enum_member.value[0],
                enum_member.value[1].format(replacement_string),
            )

        new_enum = enum.Enum(
            "MenuStrings", {enum_member.name: formatted_value}
        )[enum_member.name]
        return new_enum


class SingletonMeta(type):
    "Used to make MenuContext a singleton instance. Inherits to MenuContext."
    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class MenuContext(metaclass=SingletonMeta):
    """
    The MenuContext defines a way to interface between menus. It helps us
    maintain a reference to the current menu.
    """

    _menu = None
    __current_test_index = -1

    @property
    def saved_tests(self) -> list:
        "Our generated tests: a list of IMC dictionaries"
        return self._saved_tests

    @saved_tests.setter
    def saved_tests(self, saved_tests):
        self._saved_tests = saved_tests

    def __init__(self, menu: Menu) -> None:
        self._change_menu_to(menu)
        self._saved_tests = []

    def _change_menu_to(self, menu: Menu):
        """
        Change menu state at runtime.
        """
        self._menu = menu

        if self._menu is not None:
            self._menu.context = self

    def _initialize_test_dictionary(self, quantity):
        """
        Initializes the test list dictionary that will be generated, once we
        have the flows quantity.
        """
        self._saved_tests = create_empty_dict(quantity)
        self.__current_test_index = 0

    def _get_test_number(self):
        return self.__current_test_index + 1

    def _update_test_iterator(self):
        self.__current_test_index += 1
        if self.__current_test_index < len(self._saved_tests):
            self._change_menu_to(FlowTypeMenu())
        else:
            self._change_menu_to(None)

    def get_current_menu(self):
        return self._menu

    def get_saved_value(self, identifier):
        """Gets a value the user has entered previously, from the current test
        being generated.
        :param identifier: the identifier of the value we want to obtain."""

        return self._saved_tests[self.__current_test_index][identifier]

    def save_value(self, identifier, value):
        self._saved_tests[self.__current_test_index][identifier] = value


class Menu(ABC):
    """
    The base menu class declares methods that all specialized menus should
    implement and also provides a backreference to the MenuContext object,
    associated with the State. This backreference can be used by States to
    transition the Context to another State.
    """

    _identifier = None

    def __init__(self):
        pass

    @property
    def context(self) -> MenuContext:
        return self._context

    @context.setter
    def context(self, context: MenuContext) -> None:
        self._context = context

    @property
    def menu_strings(self):
        """:return : the menu_strings enum of the current menu."""
        return self._menu_strings

    @abstractmethod
    def next_menu(self) -> None:
        """Each menu state defines what its next menu will be here."""
        pass

    @abstractmethod
    def menu_is_complete(self):
        """Defines how the current menu will know if it has been completed.
        :return : True if current menu is complete."""
        pass

    @abstractmethod
    def save_input(self) -> None:
        """Save the input of the current menu to our test_output."""
        pass

    @abstractmethod
    def menu_action(self) -> None:
        """What the menu performs, usually I/O of data."""
        pass


class FlowQuantityMenu(Menu):
    """
    Asks the user the quantity of flows to be generated, which is equal to the
    numbe of tests to be generated."""

    _menu_strings = MenuStrings.FlowQuantity

    def menu_action(self) -> None:
        print(
            """
         Flow quantity selected: <{0}>

         0. Exit
         Press enter to continue
        """.format(
                len(self.context.saved_tests)
            )
        )
        user_input = str(input("Type flow quantity: "))

        (is_valid, sanitized_input) = _parse_user_input(user_input, int)

        if is_valid:
            flow_quantity = sanitized_input
            self.save_input(flow_quantity)

    def next_menu(self) -> None:
        self.context._change_menu_to(FlowTypeMenu())

    def save_input(self, tests_size):
        self.context._initialize_test_dictionary(tests_size)

    def menu_is_complete(self):
        return self.context.saved_tests != []


class ListSelectionMenu(Menu):

    def __init__(self, caller_menu, options, identifier):
        self._caller_menu = caller_menu
        self._options = options
        self._identifier = identifier
        self._selected_option = None

        if not isinstance(self._options, list):
            self._options = self._convert_options_to_string_list()

    def _convert_options_to_string_list(self):
        # If algorithm, grab only pattern compatible.
        if self._identifier in [
            ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
            ParameterIdentifier.DATA_ALGORITHM_TYPE,
        ]:
            if self._identifier == ParameterIdentifier.ADDRESS_ALGORITHM_TYPE:
                return get_supported_algorithm_types(PatternType.ADDRESS)
            elif self._identifier == ParameterIdentifier.DATA_ALGORITHM_TYPE:
                return get_supported_algorithm_types(PatternType.DATA)

        # if options are enums
        elif issubclass(self._options, enum.Enum):
            return get_enum_string_list(self._options)
        # if options is algorithm
        elif inspect.isclass(self._options):
            return get_class_string_list(self._options)

    def menu_action(self) -> None:
        print(
            """\

       {0}

      Selected option: <{1}>

       0. Exit
       Press enter to continue
        """.format(
                "\n       ".join(
                    f"{i+1}. {option}" for i, option in enumerate(self._options)
                ),
                self._selected_option,
            )
        )

        user_input = str(input("Select an option: "))

        (is_valid, option_index) = _parse_user_input(user_input, int)

        if is_valid:
            try:
                input_value = self._options[option_index - 1]
                self._selected_option = input_value
                self.save_input()
            except IndexError:
                pass

    def save_input(self) -> None:
        self.context.save_value(self._identifier, self._selected_option)

    def menu_is_complete(self):
        return self.context.get_saved_value(self._identifier) is not None

    def next_menu(self):
        self.context._change_menu_to(self._caller_menu)

    @property
    def menu_strings(self):
        return self._caller_menu.menu_strings


class FlowTypeMenu(Menu):
    """Asks the user the quantity of flows to be generated, which is equal to
    the number of tests to be generated."""

    _menu_strings = MenuStrings.FlowTypeSelection
    _options = IMCFlow
    _identifier = ParameterIdentifier.FLOW_TYPE

    def menu_action(self) -> None:
        if not self.menu_is_complete():
            self.context._change_menu_to(
                ListSelectionMenu(self, self._options, self._identifier)
            )
        else:
            self.next_menu()

    @property
    def identifier(self):
        return self._identifier

    def next_menu(self) -> None:
        self.context._change_menu_to(GlobalExecutionMenu())

    def save_input(self, selected_flow):
        self.context.save_value(self._identifier, selected_flow)

    def menu_is_complete(self):
        return self.context.get_saved_value(self._identifier) is not None


class GlobalExecutionMenu(Menu):
    """Handles global parameters menu."""

    _menu_strings = MenuStrings.GlobalExecution
    _options = list(IMCControl.PARAMETERS)
    _filter = [ParameterName.IMC_CONTROL_FLOW.value]

    def menu_action(self) -> None:
        self.context._change_menu_to(MultipleParametersMenu(self))

    def next_menu(self) -> None:
        self.context._change_menu_to(FlowParametersMenu())

    def save_input(self, input):
        (identifier, value) = input
        self.context.save_value(identifier, value)

    def menu_is_complete(self):
        for option in self._options:
            if (
                option.is_required
                and self.context.get_saved_value(option.identifier) is None
            ):
                return False
        return True


class FlowParametersMenu(Menu):
    """Handles the parameters of the selected flow."""

    _menu_strings = MenuStrings.FlowParameters
    _options = []
    _filter = [ParameterIdentifier.FLOW_TYPE]

    def __init__(self):
        selected_flow = MenuContext().get_saved_value(
            ParameterIdentifier.FLOW_TYPE
        )
        flow_object = IMCFlow.Base.getSubclassByName(selected_flow)
        self._options = list(flow_object().PARAMETERS)
        self._options = sorted(
            self._options, key=lambda x: x.is_required, reverse=True
        )
        self._algorithm_type = flow_object.type

        self._menu_strings = MenuStrings._format_description(
            self._menu_strings, selected_flow
        )

    def menu_action(self) -> None:
        self.context._change_menu_to(MultipleParametersMenu(self))

    def next_menu(self) -> None:
        """Goes to the next menu: the algorithm parameters menu.
        Before, we obtain the pattern type from the flow."""
        address_algorithm = self.context.get_saved_value(
            ParameterIdentifier.ADDRESS_ALGORITHM_TYPE
        )
        data_algorithm = self.context.get_saved_value(
            ParameterIdentifier.DATA_ALGORITHM_TYPE
        )

        if self._algorithm_type == PatternType.ADDRESS:
            selected_algorithm = address_algorithm
            selected_pattern = PatternType.ADDRESS
            algorithm_tuple = [(selected_algorithm, selected_pattern)]

        elif self._algorithm_type == PatternType.DATA:
            selected_algorithm = data_algorithm
            selected_pattern = PatternType.DATA
            algorithm_tuple = [(selected_algorithm, selected_pattern)]
        else:
            algorithm_tuple = [
                (data_algorithm, PatternType.DATA),
                (address_algorithm, PatternType.ADDRESS),
            ]

        self.context._change_menu_to(AlgorithmParametersMenu(algorithm_tuple))

    def save_input(self, input):
        (identifier, value) = input
        self.context.save_value(identifier, value)

    def menu_is_complete(self):
        for option in self._options:
            set_option = self.context.get_saved_value(option.identifier)
            if option.is_required and set_option is None:
                return False
        return True


class MultipleParametersMenu(Menu):
    """Helps us receive a list of parameters of any data,
    and display the list option to the user. This allows avoiding hardcoding
    parameters per menu, and have new menu options appear when added to IMC,
    without changing the menu class.
    """

    def __init__(self, caller_menu):
        self._caller_menu = caller_menu
        self._original_parameters = caller_menu._options
        self._selected_option = None
        try:
            self._filter = caller_menu._filter
        except AttributeError:
            self._filter = []
        self._set_default_values()

    def filter_menu_options(self):
        self._filtered_parameters = filter(
            lambda x: x.parameter_name not in self._filter,
            list(self._original_parameters),
        )
        self._filtered_parameters, string_options = list(
            tee(self._filtered_parameters)
        )
        self._string_options = [
            f"""{x.parameter_name.capitalize()}: <{
                self.context.get_saved_value(x.identifier)
        if (self.context.get_saved_value(x.identifier) is not None
        or x.is_required)
        else "optional"}>"""
            for x in string_options
        ]
        self._filtered_parameters = list(self._filtered_parameters)

    def menu_action(self) -> None:

        self.filter_menu_options()

        print(
            """\

       {0}

      Selected option: <{1}>

       0. Exit
       Press enter to continue
        """.format(
                "\n       ".join(
                    f"{i+1}. {option}"
                    for i, option in enumerate(self._string_options)
                ),
                self._selected_option,
            )
        )

        user_input = str(input("Select an option: "))

        (is_valid, parameter_index) = _parse_user_input(user_input, int)

        if is_valid:

            try:

                user_selected_value = self._filtered_parameters[
                    parameter_index - 1
                ]
                self._selected_option = self._string_options[
                    parameter_index - 1
                ]

                data_type = user_selected_value.data_type

                if _data_requires_additional_menu(data_type):
                    user_input = _handle_specialized_data(user_selected_value)
                    if user_input is not None:
                        self.save_input(
                            (user_selected_value.identifier, user_input)
                        )
                    self._selected_option = None

                else:
                    user_input = input("Type value: ")
                    (_, user_input) = _parse_user_input(
                        user_input, user_selected_value.data_type
                    )
                    self.save_input(
                        (user_selected_value.identifier, user_input)
                    )
                    self._selected_option = None

            except IndexError:
                pass

    @property
    def menu_strings(self):
        return self._caller_menu._menu_strings

    def next_menu(self) -> None:
        self._caller_menu.next_menu()

    def _set_default_values(self):
        try:
            for parameter in self._original_parameters:  # Set default params
                if (
                    parameter.inner_value is not None
                    and parameter.inner_value != ""
                ):
                    MenuContext().save_value(
                        parameter.identifier, parameter.inner_value
                    )
        except AttributeError:
            # No default inner value has been defined, continue iteration.
            pass

    def save_input(self, data_tuple):
        (identifier, user_selected) = data_tuple
        self.context.save_value(identifier, str(user_selected))

        # Handle quirks that comes from dynamic parameters.
        # If iterations is set, time_to_execute is None, and viceversa
        # (from time Menu).
        if identifier == ParameterIdentifier.GLOBAL_ITERATIONS:
            self.context.save_value(
                ParameterIdentifier.GLOBAL_TIME_TO_EXECUTE, None
            )

    def menu_is_complete(self):
        return self._caller_menu.menu_is_complete()


class TimeSelectionMenu(Menu):
    """Handles getting IMC time type parameter."""

    _menu_strings = MenuStrings.IMCTimeSelection
    _options = IMCTimeType

    @property
    def identifier(self):
        return self._identifier

    def __init__(self, caller_menu, identifier):
        self._caller_menu = caller_menu
        self._identifier = identifier
        self._time_unit = None
        self._time_value = None
        MenuContext().save_value(self._identifier, None)  # Reset time

    def menu_action(self) -> None:
        self._time_unit = self.context.get_saved_value(self._identifier)
        if self._time_unit is None:
            self.context._change_menu_to(
                ListSelectionMenu(self, self._options, self._identifier)
            )

        elif self._time_value is None:  # Get number time quantity
            user_input = input(f"Type number of {self._time_unit.lower()}: ")
            (is_valid, sanitized_input) = _parse_user_input(user_input, int)
            if is_valid:
                self.save_input(sanitized_input)
        else:
            self.next_menu()

    def next_menu(self) -> None:
        if self._time_value is not None:
            self.context._change_menu_to(self._caller_menu)
        else:
            self.context._change_menu_to(self)

    def save_input(self, time_selection):
        if str(time_selection).isnumeric():
            self._time_value = str(time_selection) + (self._time_unit)
            self.context.save_value(self._identifier, self._time_value)

            # If time_to_execute is set, iterations is None, and viceversa.
            if self._identifier == ParameterIdentifier.GLOBAL_TIME_TO_EXECUTE:
                self.context.save_value(
                    ParameterIdentifier.GLOBAL_ITERATIONS, None
                )

    def menu_is_complete(self):
        return self._time_unit is not None


class AlgorithmParametersMenu(Menu):
    """Handles algorithm parameters type."""

    _menu_strings = MenuStrings.AlgorithmParameters
    _options = []
    _filter = [ParameterName.ALGORITHM_TYPE]

    def __init__(self, algorithms):
        self._algorithms = algorithms
        algorithm = algorithms.pop()
        (algorithm_name, algorithm_pattern) = algorithm
        self._options = list(
            IMCAlgorithm.Base.getSubclassByName(algorithm_name)(
                algorithm_pattern
            ).PARAMETERS
        )
        self._menu_strings = MenuStrings._format_description(
            self._menu_strings, algorithm_name
        )

    def menu_action(self) -> None:
        self.context._change_menu_to(MultipleParametersMenu(self))

    def next_menu(self) -> None:
        if len(self._algorithms) != 0:
            self.context._change_menu_to(
                AlgorithmParametersMenu(self._algorithms)
            )
        else:
            self.context._change_menu_to(MemoryTypeMenu())

    def save_input(self, input):
        (identifier, value) = input
        self.context.save_value(identifier, value)

    def menu_is_complete(self):
        for option in self._options:
            set_option = self.context.get_saved_value(option.identifier)
            if option.is_required and set_option is None:
                return False
        return True


class MemoryTypeMenu(Menu):
    __ALLOCATOR_IDENTIFIER = "Allocator"
    __MEMORY_TYPE_IDENTIFIER = "Memory Type"
    _menu_strings = MenuStrings.MemoryType

    def __init__(self):
        self.format_memory_menu_strings()
        self._options = [
            IMCParameter(self.__ALLOCATOR_IDENTIFIER, True, IMCMemory),
            IMCParameter(self.__MEMORY_TYPE_IDENTIFIER, True, MemoryType),
        ]
        MenuContext().save_value(self.__ALLOCATOR_IDENTIFIER, None)
        MenuContext().save_value(self.__MEMORY_TYPE_IDENTIFIER, None)

    def menu_action(self):
        memory_allocator = self.context.get_saved_value(
            self.__ALLOCATOR_IDENTIFIER
        )
        memory_type = self.context.get_saved_value(
            self.__MEMORY_TYPE_IDENTIFIER
        )
        if not memory_allocator and not memory_type:
            self.context._change_menu_to(MultipleParametersMenu(self))
        else:
            if self.menu_is_complete():
                self.context._change_menu_to(None)

    def format_memory_menu_strings(self):
        memory_block_amount = MenuContext().get_saved_value(
            ParameterIdentifier.MEMORY_BLOCK_AMOUNT
        )
        group_total_memory = MenuContext().get_saved_value(
            ParameterIdentifier.MEMORY_GROUP_OVERALL
        )

        if memory_block_amount is None:
            memory_block_amount = 0

        if group_total_memory is None:
            group_total_blocks = 0
        else:
            group_block_size = MenuContext().get_saved_value(
                ParameterIdentifier.MEMORY_GROUP_SIZE_IN_BYTES
            )
            group_total_blocks = int(group_total_memory) / int(group_block_size)

        self._menu_strings = MenuStrings._format_description(
            self._menu_strings, [memory_block_amount, int(group_total_blocks)]
        )

    def save_input(self) -> None:
        pass

    def next_menu(self) -> None:
        memory_allocator = self.context.get_saved_value(
            self.__ALLOCATOR_IDENTIFIER
        )
        memory_type = self.context.get_saved_value(
            self.__MEMORY_TYPE_IDENTIFIER
        )
        if memory_allocator and memory_type:
            memory_type = MemoryType[memory_type]
            memory_class = IMCMemory.Base.getSubclassByName(memory_allocator)
            memory_class = memory_class(memory_type)
            memory_options = memory_class.PARAMETERS
            if memory_type == MemoryType.BLOCK:
                self.context.save_value(
                    ParameterIdentifier.MEMORY_BLOCK_ALLOCATOR_TYPE,
                    memory_allocator,
                )
                memory_options = memory_options.union(
                    {
                        IMCParameter(
                            ParameterIdentifier.MEMORY_BLOCK_AMOUNT, True, int
                        )
                    }
                )
            else:
                self.context.save_value(
                    ParameterIdentifier.MEMORY_GROUP_BLOCK_TYPE,
                    memory_allocator,
                )

            self.context._change_menu_to(
                MemoryParametersMenu(memory_options, memory_type)
            )
        else:
            memory_block_amount = MenuContext().get_saved_value(
                ParameterIdentifier.MEMORY_BLOCK_AMOUNT
            )
            group_total_memory = MenuContext().get_saved_value(
                ParameterIdentifier.MEMORY_GROUP_OVERALL
            )
            if memory_block_amount or group_total_memory:
                self.context._update_test_iterator()

    def menu_is_complete(self):
        memory_allocator = self.context.get_saved_value(
            self.__ALLOCATOR_IDENTIFIER
        )
        memory_type = self.context.get_saved_value(
            self.__MEMORY_TYPE_IDENTIFIER
        )
        if memory_allocator and memory_type:
            return True
        else:
            memory_block_amount = MenuContext().get_saved_value(
                ParameterIdentifier.MEMORY_BLOCK_AMOUNT
            )
            group_total_memory = MenuContext().get_saved_value(
                ParameterIdentifier.MEMORY_GROUP_OVERALL
            )
            return memory_block_amount or group_total_memory


class MemoryParametersMenu(Menu):
    """Handles getting memory parameters."""

    _menu_strings = MenuStrings.MemoryParameters
    _options = []
    _filter = [
        ParameterIdentifier.MEMORY_BLOCK_ALLOCATOR_TYPE,
        ParameterName.MEMORY_ALLOCATOR_TYPE,
        ParameterIdentifier.MEMORY_GROUP_BLOCK_TYPE,
    ]

    def __init__(self, options, memory_type):
        self._options = sorted(options, key=lambda x: x.identifier)
        self._menu_strings = MenuStrings._format_description(
            self._menu_strings, memory_type.name
        )

    def menu_action(self) -> None:
        self.context._change_menu_to(MultipleParametersMenu(self))

    def next_menu(self) -> None:
        self.context._change_menu_to(MemoryTypeMenu())

    def save_input(self, input):
        (identifier, value) = input
        self.context.save_value(identifier, value)

    def menu_is_complete(self):
        for option in self._options:
            if option.identifier in self._filter:
                continue
            set_option = self.context.get_saved_value(option.identifier)
            if option.is_required and set_option is None:
                return False
        return True
