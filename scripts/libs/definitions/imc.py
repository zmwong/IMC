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

"""This module defines values used for the orchestration script and its
libraries."""

from dataclasses import dataclass, field
import enum


TOOL_NAME = "Intelligent Memory Checker"
REQ_VER = (3, 7)
TOOL_VERSION = "1.9"

MEM_USE_DFLT = 95


TargetEnvironment = [
    "LINUX",
    "SVOS",
    "SHARED_LIBRARY",
    "SVOS_DEBIAN_PACKAGE",
    "LINUX_ONLY",
]


class BinaryNames:
    REGULAR_BINARY = "IntelligentMemoryChecker_tool"
    VERSION_BINARY = f"IntelligentMemoryChecker_tool-{TOOL_VERSION}"
    WINDOWS_BINARY = VERSION_BINARY + ".exe"
    DEBIAN_PACKAGE_BINARY = "intelligentmemorychecker"


class PyFrameworkExecutables:
    IMC_RUNNER = "runIMC.py"
    IMC_LAUNCHER = "launchIMC.py"
    IMC_COMPILER = "compileIMC.py"


class PatternType(enum.Enum):
    """IMC Supported patterns for algorithms. It can be both data and address
    or one of them."""

    UNKNOWN_PATTERN = 1
    DATA = 2
    ADDRESS = 3
    DATA_AND_ADDRESS = 4


class MemoryType(enum.Enum):
    BLOCK = 1
    GROUP = 2


class IMCTimeType(enum.Enum):
    """IMC supported time types, and it's maximum allowed value."""

    SECONDS = (315400000,)
    MINUTES = (5256666,)
    HOURS = (87611,)
    DAYS = (3650,)
    WEEKS = (521,)
    MONTHS = (120,)


class IMCOpcodeType(enum.Enum):
    """IMC supported opcodes"""

    LEGACY = (1,)
    AVX_VMOVDQU = (2,)
    AVX_VMOVNTDQ = (3,)
    SSE_MOVDQU = (4,)
    SSE_MOVDQA = (5,)
    AVX512_VMOVDQU = (6,)
    AVX512_VMOVNTDQ = 7


class IMCMappingMode(enum.Enum):
    """IMC supported mapping modes for SVOS memory"""

    SHARED = (1,)
    PRIVATE = 2


class ListTypes(enum.Enum):
    """Different kind of list parameters that IMC can have,
    since they are declared differently in tests.
    """

    Pattern_List = (1,)
    March_Element = 2


class IMCParameter:
    """Defines the structure an IMC configuration parameter has.
    identifier: The way we differentiate between parameters INSIDE the
    codebase.

    is_required: Declare wheter the parameter is necessary to continue test
    generation.

    data_type: The type of the data, can be a primitive or a class. Necessary
    to validate if the test has the correct type, or for interactive test
    creation, to know how to request the parameter to the user.

    parameter_name: Unlike identifier, parameter_name defines the exact string
    the test has, as its defined and required to be in IMC.
    Ex. 'global_iterations' is an identifier, but its parameter_name is
    'iterations'.
    'global_iterations' will be shown in the test as
    '<iterations>1</iterations>'
    We use 'global_iterations' to differentiate it with 'iterations' since one
    belongs to all test file iterations and the other to a flow only.
    Both will be written as 'iterations'.

    inner_value: The actual value of the parameter. If defined, it will be
    used as a default value.
    """

    def __init__(
        self,
        identifier,
        is_required,
        data_type,
        parameter_name="",
        inner_value: str = "",
    ):
        self.identifier = identifier
        self.is_required = is_required
        self.data_type = data_type
        self.inner_value = inner_value

        # if parameter_name is empty, we use the identifier as a name
        if not parameter_name:
            self.parameter_name = self.identifier
        else:
            self.parameter_name = parameter_name


class ParameterIdentifier(str, enum.Enum):
    """Each IMC parameter has an identifier, defined here.
    The identifiers are also used to define the columns the test dictionary we
    use for test generation will have. All dictionary columns are defined
    here."""

    SECONDARY = "secondary"
    NUMBER_CACHE_LINES = "number_cache_lines"
    CHANGE_WEDGE = "change_wedge"
    BLOCKS_PER_SET = "blocks_per_set"
    MAX_SETS_TO_EVICT = "max_sets_to_evict"
    WAY_STRIDE = "way_stride"
    SET_STRIDE = "set_stride"
    CHANGE_PIVOT = "change_pivot"
    PATTERN_LIST = "pattern_list"
    NUMBER_BYTES_TO_REPEAT = "number_bytes_to_repeat"
    MATCH_VALUE = "match_value"
    SAME_ADDRESS = "same_address"
    WRITE_ONCE = "write_once"
    PARTIAL_WRITE = "partial_write"
    BYPASS_WRITE_PHASE = "bypass_write_phase"
    BYPASS_READ_PHASE = "bypass_read_phase"
    DATA_BURSTS = "data_bursts"
    WEDGE_SIZE = "wedge_size"
    PIVOT_STATIC_VALUE = "pivot_static_value"
    PIVOT_INITIAL_POSITION = "pivot_initial_position"
    MATCH_MASK = "match_mask"
    MARCH_ELEMENT = "march_element"
    ADDRESS_SKIP_BASE_PATTERN = "address_skip_base_pattern"
    DATA_SKIP_BASE_PATTERN = "data_skip_base_pattern"
    RESTART_ALGORITHM_AT_ITERATION = "restart_algorithm_at_iteration"
    DATA_SEED = "data_seed"
    ADDRESS_SEED = "address_seed"
    MEMORY_GROUP_SIZE_IN_BYTES = "memory_group_size_in_bytes"
    MEMORY_GROUP_BLOCK_TYPE = "memory_group_block_type"
    MEMORY_GROUP_MAPPING_MODE = "memory_group_mapping_mode"
    MEMORY_GROUP_OVERALL = "overall_memory_group"
    MEMORY_SIZE_IN_BYTES = "memory_size_in_bytes"
    MEMORY_GROUP_TARGET_PATH = "memory_group_target_path"
    MEMORY_GROUP_PHYSICAL_ADDRESS_HIGH = "memory_group_physical_address_high"
    MEMORY_GROUP_PHYSICAL_ADDRESS_LOW = "memory_group_physical_address_low"
    MEMORY_GROUP_PHYSICAL_ADDRESS = "memory_group_physical_address"
    MEMORY_GROUP_ENABLE_READ_MAPPING = "memory_group_enable_read_mapping"
    MEMORY_GROUP_ENABLE_WRITE_MAPPING = "memory_group_enable_write_mapping"
    MEMORY_GROUP_ENABLE_EXEC_MAPPING = "memory_group_enable_exec_mapping"
    MEMORY_GROUP_ALLOW_ALIASING = "memory_group_allow_aliasing"
    MEMORY_BLOCK_TARGET_PATH = "memory_block_target_path"
    MEMORY_BLOCK_PHYSICAL_ADDRESS_HIGH = "memory_block_physical_address_high"
    MEMORY_BLOCK_PHYSICAL_ADDRESS_LOW = "memory_block_physical_address_low"
    MEMORY_BLOCK_PHYSICAL_ADDRESS = "memory_block_physical_address"
    MEMORY_BLOCK_ENABLE_READ_MAPPING = "memory_block_enable_read_mapping"
    MEMORY_BLOCK_ENABLE_WRITE_MAPPING = "memory_block_enable_write_mapping"
    MEMORY_BLOCK_ENABLE_EXEC_MAPPING = "memory_block_enable_exec_mapping"
    MEMORY_BLOCK_ALLOW_ALIASING = "memory_block_allow_aliasing"
    MEMORY_BLOCK_ALLOCATOR_TYPE = "memory_block_type"
    MEMORY_BLOCK_MAPPING_MODE = "memory_mapping_mode"
    MEMORY_BLOCK_AMOUNT = "memory_block_amount"
    DATA_UPPER_LIMIT_PATTERN = "data_upper_limit_pattern"
    DATA_LOWER_LIMIT_PATTERN = "data_lower_limit_pattern"
    ADDRESS_UPPER_LIMIT_PATTERN = "address_upper_limit_pattern"
    ADDRESS_LOWER_LIMIT_PATTERN = "address_lower_limit_pattern"
    DATA_INCREMENTOR = "data_incrementor"
    ADDRESS_INCREMENTOR = "address_incrementor"
    DATA_DECREMENTOR = "data_decrementor"
    ADDRESS_DECREMENTOR = "address_decrementor"
    CONTINUE_ON_FAIL = "continue_on_fail"
    GLOBAL_ITERATIONS = "global_iterations"
    GLOBAL_TIME_TO_EXECUTE = "global_time_to_execute"
    GLOBAL_TIME_UNIT = "global_time_unit"
    DATA_PATTERN_COUNT = "data_pattern_count"
    ADDRESS_PATTERN_COUNT = "address_pattern_count"
    CONSTANT_PATTERN = "constant_pattern"
    ITERATIONS = "iterations"
    OPCODE = "opcode"
    ALIGNMENT = "alignment"
    DATA_ALGORITHM_TYPE = "data_algorithm_type"
    ADDRESS_ALGORITHM_TYPE = "address_algorithm_type"
    FLOW_TYPE = "flow_type"
    EXPECTED_VALUE = "expected_value"
    FILE_NAME = "file_name"
    COLUMN1 = "Column1"


class ParameterName(str, enum.Enum):
    """Defines a list of strings the test will be written with."""

    ROOT = "IntelligentMemoryChecker"
    IMC_CONTROL_BLOCK = "IMC_configuration"
    IMC_CONTROL_FLOW = "flow"
    TIME_TO_EXECUTE = "time_to_execute"
    ALGORITHM = "algorithm"
    ALGORITHM_TYPE = "algorithm_type"
    ADDRESS_ALGORITHM = "address_algorithm"
    DATA_ALGORITHM = "data_algorithm"
    PATTERN_COUNT = "pattern_count"
    SKIP_BASE_PATTERN = "skip_base_pattern"
    LOWER_LIMIT_PATTERN = "lower_limit_pattern"
    UPPER_LIMIT_PATTERN = "upper_limit_pattern"
    SEED = "seed"
    MEMORY_BLOCK = "memory_block"
    MEMORY_ALLOCATOR_TYPE = "memory_block_type"
    MEMORY_SIZE = "size_in_bytes"
    MEMORY_BLOCK_GROUP = "memory_block_group"
    MEMORY_BLOCK_GROUP_OVERALL = "overall_memory"
    MEMORY_BLOCK_GROUP_ID = "memory_block_group_id_0"
    MEMORY_BLOCK_ID = "memory_block_"
    MEMORY_MAPPING_MODE = "memory_mapping_mode"
    TARGET_PATH = "target_path"
    PHYSICAL_ADDRESS_HIGH = "physical_address_high"
    PHYSICAL_ADDRESS_LOW = "physical_address_low"
    PHYSICAL_ADDRESS = "physical_address"
    ENABLE_READ_MAPPING = "enable_read_mapping"
    ENABLE_WRITE_MAPPING = "enable_write_mapping"
    ENABLE_EXEC_MAPPING = "enable_exec_mapping"
    ALLOW_ALIASING = "allow_aliasing"
    INCREMENTOR = "incrementor"
    DECREMENTOR = "decrementor"

    def __str__(self):
        return self.value


class IMCAlgorithm:
    """All supported algorithms.
    Every algorithm is derived from base algorithm, which contains common
    parameters all algorithms have.
    All parameters each algorithm supports is defined inside the 'PARAMETERS'
    set, of 'IMCParameter' type."""

    @dataclass
    class Base:
        type: PatternType
        pattern_compability: PatternType = field(init=False)
        NAME: str = "UNKNOWN_ALGORITHM_NAME"
        _algorithm_type: str = field(init=False)
        _pattern_count: str = field(init=False)
        _skip_base_pattern: str = field(init=False)
        _seed: str = field(init=False)
        _lower_limit_pattern: str = field(init=False)
        _upper_limit_pattern: str = field(init=False)
        _incrementor: str = field(init=False)
        _decrementor: str = field(init=False)
        _base_parameters: set = field(init=False)

        PARAMETERS = {}

        @classmethod
        def getSubclassByName(cls, name):
            """Helper function to get an specialized algorithm by it's name.
            :param name: name of the algorithm.
            :return: the specialized algorithm subclass.
            If not found returns None"""
            for subclass in cls.__subclasses__():
                if subclass.NAME == name:
                    return subclass
            return None

        @classmethod
        def getTypes(cls):
            """Get all specialized algorithm subclasses.
            :return: List of specialized algorithms."""
            return cls.__subclasses__()

        @classmethod
        def getTypesByPatternCompability(cls, pattern_type):
            """Get compatible  algorithm subclasses, given a pattern.
            :return: List of specialized algorithms."""
            return [
                algorithm
                for algorithm in cls.__subclasses__()
                if algorithm.pattern_compability == PatternType.DATA_AND_ADDRESS
                or algorithm.pattern_compability == pattern_type
            ]

        def __post_init__(self):
            """Defines the identifier of pattern-dependant parameters.
            Runs after initialization, when a pattern has been provided.
            Merges base parameters with specialized ones."""
            if self.type == PatternType.ADDRESS:
                self._algorithm_type = (
                    ParameterIdentifier.ADDRESS_ALGORITHM_TYPE
                )
                self._pattern_count = ParameterIdentifier.ADDRESS_PATTERN_COUNT
                self._skip_base_pattern = (
                    ParameterIdentifier.ADDRESS_SKIP_BASE_PATTERN
                )
                self._seed = ParameterIdentifier.ADDRESS_SEED
                self._lower_limit_pattern = (
                    ParameterIdentifier.ADDRESS_LOWER_LIMIT_PATTERN
                )
                self._upper_limit_pattern = (
                    ParameterIdentifier.ADDRESS_UPPER_LIMIT_PATTERN
                )
                self._incrementor = ParameterIdentifier.ADDRESS_INCREMENTOR
                self._decrementor = ParameterIdentifier.ADDRESS_DECREMENTOR

            elif self.type == PatternType.DATA:
                self._algorithm_type = ParameterIdentifier.DATA_ALGORITHM_TYPE
                self._pattern_count = ParameterIdentifier.DATA_PATTERN_COUNT
                self._skip_base_pattern = (
                    ParameterIdentifier.DATA_SKIP_BASE_PATTERN
                )
                self._seed = ParameterIdentifier.DATA_SEED
                self._lower_limit_pattern = (
                    ParameterIdentifier.DATA_LOWER_LIMIT_PATTERN
                )
                self._upper_limit_pattern = (
                    ParameterIdentifier.DATA_UPPER_LIMIT_PATTERN
                )
                self._incrementor = ParameterIdentifier.DATA_INCREMENTOR
                self._decrementor = ParameterIdentifier.DATA_DECREMENTOR

            self._base_parameters = {
                IMCParameter(
                    self._algorithm_type,
                    True,
                    str,
                    ParameterName.ALGORITHM_TYPE,
                ),
                IMCParameter(
                    self._pattern_count, False, str, ParameterName.PATTERN_COUNT
                ),
                IMCParameter(
                    self._skip_base_pattern,
                    False,
                    bool,
                    ParameterName.SKIP_BASE_PATTERN,
                ),
            }
            self.init_parameters()
            self.PARAMETERS = self._base_parameters.union(self.PARAMETERS)

    @dataclass
    class ByteAdd(Base):
        NAME: str = "BYTE_ADD"
        pattern_compability = PatternType.DATA

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    ParameterIdentifier.NUMBER_BYTES_TO_REPEAT, False, int
                ),
                IMCParameter(self._seed, False, int, ParameterName.SEED),
            }

    @dataclass
    class Constant(Base):
        NAME: str = "CONSTANT"
        pattern_compability = PatternType.DATA

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(ParameterIdentifier.CONSTANT_PATTERN, False, int)
            }

    @dataclass
    class DancingBits(Base):
        NAME: str = "DANCING_BITS"
        pattern_compability = PatternType.DATA
        PARAMETERS = {}

        def init_parameters(self):
            pass

    @dataclass
    class Decrement(Base):
        NAME: str = "DECREMENT"
        pattern_compability = PatternType.DATA_AND_ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._lower_limit_pattern,
                    False,
                    int,
                    ParameterName.LOWER_LIMIT_PATTERN,
                ),
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
                IMCParameter(
                    self._decrementor, False, int, ParameterName.DECREMENTOR
                ),
            }

    @dataclass
    class FastRandom(Base):
        NAME: str = "FAST_RANDOM"
        pattern_compability = PatternType.DATA_AND_ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._lower_limit_pattern,
                    False,
                    int,
                    ParameterName.LOWER_LIMIT_PATTERN,
                ),
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
                IMCParameter(self._seed, False, int, ParameterName.SEED),
            }

    @dataclass
    class GLFSR(Base):
        NAME: str = "GLFSR"
        pattern_compability = PatternType.DATA_AND_ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
                IMCParameter(self._seed, False, int, ParameterName.SEED),
            }

    @dataclass
    class Increment(Base):
        NAME: str = "INCREMENT"
        pattern_compability = PatternType.DATA_AND_ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._incrementor, False, int, ParameterName.INCREMENTOR
                ),
            }

    @dataclass
    class LFSR(Base):
        NAME: str = "LFSR"
        pattern_compability = PatternType.DATA_AND_ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
                IMCParameter(self._seed, False, int, ParameterName.SEED),
            }

    @dataclass
    class Negator(Base):
        NAME: str = "NEGATOR"
        pattern_compability = PatternType.DATA

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(self._seed, False, int, ParameterName.SEED),
            }

    @dataclass
    class PatternList(Base):
        NAME: str = "PATTERN_LIST"
        pattern_compability = PatternType.DATA

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    ParameterIdentifier.PATTERN_LIST,
                    False,
                    (list, ListTypes.Pattern_List),
                )
            }

    @dataclass
    class Pivot(Base):
        NAME: str = "PIVOT"
        pattern_compability = PatternType.ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._lower_limit_pattern,
                    False,
                    int,
                    ParameterName.LOWER_LIMIT_PATTERN,
                ),
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
                IMCParameter(ParameterIdentifier.CHANGE_PIVOT, False, bool),
                IMCParameter(
                    ParameterIdentifier.PIVOT_INITIAL_POSITION, False, int
                ),
            }

    @dataclass
    class SetAssociative(Base):
        NAME: str = "SET_ASSOCIATIVE"
        pattern_compability = PatternType.ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._lower_limit_pattern,
                    False,
                    int,
                    ParameterName.LOWER_LIMIT_PATTERN,
                ),
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
                IMCParameter(ParameterIdentifier.SET_STRIDE, False, int),
                IMCParameter(ParameterIdentifier.WAY_STRIDE, False, int),
                IMCParameter(ParameterIdentifier.BLOCKS_PER_SET, False, int),
                IMCParameter(ParameterIdentifier.MAX_SETS_TO_EVICT, False, int),
            }

    @dataclass
    class Shifting(Base):
        NAME: str = "SHIFTING"
        pattern_compability = PatternType.DATA

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(self._seed, False, int, ParameterName.SEED),
            }

    @dataclass
    class WalkingOne(Base):
        NAME: str = "WALKING_ONE"
        pattern_compability = PatternType.DATA_AND_ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._lower_limit_pattern,
                    False,
                    int,
                    ParameterName.LOWER_LIMIT_PATTERN,
                ),
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
            }

    @dataclass
    class WalkingZero(Base):
        NAME: str = "WALKING_ZERO"
        pattern_compability = PatternType.DATA_AND_ADDRESS

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._lower_limit_pattern,
                    False,
                    int,
                    ParameterName.LOWER_LIMIT_PATTERN,
                ),
                IMCParameter(
                    self._upper_limit_pattern,
                    False,
                    int,
                    ParameterName.UPPER_LIMIT_PATTERN,
                ),
            }

    @dataclass
    class Wedge(Base):
        NAME: str = "WEDGE"
        pattern_compability = PatternType.DATA

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(ParameterIdentifier.WEDGE_SIZE, False, int),
                IMCParameter(ParameterIdentifier.CHANGE_WEDGE, False, bool),
            }

    @dataclass
    class Xtalk(Base):
        NAME: str = "XTALK"
        pattern_compability = PatternType.DATA

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    ParameterIdentifier.NUMBER_CACHE_LINES, False, int
                ),
                IMCParameter(self._seed, False, int, ParameterName.SEED),
                IMCParameter(ParameterIdentifier.SECONDARY, False, bool),
            }


# IMCControl class
@dataclass
class IMCControl:
    """All supported parameters for IMC configuration."""

    PARAMETERS = {
        IMCParameter(
            ParameterIdentifier.FLOW_TYPE,
            True,
            str,
            ParameterName.IMC_CONTROL_FLOW,
        ),
        IMCParameter(
            ParameterIdentifier.GLOBAL_TIME_TO_EXECUTE,
            False,
            IMCTimeType,
            ParameterName.TIME_TO_EXECUTE,
        ),
        IMCParameter(ParameterIdentifier.CONTINUE_ON_FAIL, False, bool),
        IMCParameter(
            ParameterIdentifier.GLOBAL_ITERATIONS,
            False,
            int,
            ParameterIdentifier.ITERATIONS,
            "1",
        ),
    }


class IMCFlow:
    """All supported flows.
    Every flow is derived from base flow, which contains common parameters
    all flows have.
    All parameters each flow supports is defined inside the 'PARAMETERS' set,
    of 'IMCParameter' type."""

    @dataclass
    class Base:
        type = PatternType.UNKNOWN_PATTERN
        NAME: str = "UNKNOWN_FLOW_NAME"
        _BASE_PARAMETERS: set = field(
            default_factory=lambda: {
                IMCParameter(ParameterIdentifier.FLOW_TYPE, True, str),
                IMCParameter(ParameterIdentifier.OPCODE, True, IMCOpcodeType),
                IMCParameter(
                    ParameterIdentifier.BYPASS_WRITE_PHASE, False, bool
                ),
                IMCParameter(
                    ParameterIdentifier.BYPASS_READ_PHASE, False, bool
                ),
                IMCParameter(ParameterIdentifier.CONTINUE_ON_FAIL, False, bool),
                IMCParameter(ParameterIdentifier.ITERATIONS, False, int),
                IMCParameter(ParameterIdentifier.WRITE_ONCE, False, bool),
                IMCParameter(ParameterIdentifier.MATCH_MASK, False, str),
                IMCParameter(ParameterIdentifier.MATCH_VALUE, False, str),
                IMCParameter(ParameterIdentifier.ALIGNMENT, False, int),
                IMCParameter(ParameterIdentifier.PARTIAL_WRITE, False, bool),
                IMCParameter(
                    ParameterIdentifier.RESTART_ALGORITHM_AT_ITERATION,
                    False,
                    bool,
                ),
            }
        )
        PARAMETERS = {}

        @classmethod
        def getTypes(cls):
            """Get all specialized flow subclasses.
            :return: List of specialized flows."""
            return cls.__subclasses__()

        @classmethod
        def getSubclassByName(cls, name):
            """Helper function to get an specialized flow by it's name.
            :param name: name of the flow.
            :return: the specialized flow subclass.
            If not found returns None"""
            for subclass in cls.__subclasses__():
                if subclass.NAME == name:
                    return subclass
            return None

        def __post_init__(self):
            """Merges base parameters with specialized ones."""
            self.PARAMETERS = self._BASE_PARAMETERS.union(self.PARAMETERS)

    @dataclass
    class DataHarasser(Base):
        type = PatternType.DATA
        NAME: str = "DATA_HARASSER"
        PARAMETERS = {
            IMCParameter(
                ParameterIdentifier.DATA_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.ALGORITHM,
            )
        }

    @dataclass
    class AddressHarasser(Base):
        type = PatternType.ADDRESS
        NAME: str = "ADDRESS_HARASSER"
        PARAMETERS = {
            IMCParameter(
                ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.ALGORITHM,
            )
        }

    @dataclass
    class March(Base):
        type = PatternType.DATA
        NAME: str = "MARCH"
        PARAMETERS = {
            IMCParameter(
                ParameterIdentifier.DATA_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.DATA_ALGORITHM,
            ),
            IMCParameter(
                ParameterIdentifier.MARCH_ELEMENT,
                True,
                (list, ListTypes.March_Element),
            ),
        }

    @dataclass
    class MarchSimpleStatic(Base):
        type = PatternType.DATA_AND_ADDRESS
        NAME: str = "MARCH_SIMPLE_STATIC"
        PARAMETERS = {
            IMCParameter(
                ParameterIdentifier.DATA_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.DATA_ALGORITHM,
            ),
            IMCParameter(
                ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.ADDRESS_ALGORITHM,
            ),
        }

    @dataclass
    class Custom(Base):
        type = PatternType.DATA_AND_ADDRESS
        NAME: str = "CUSTOM"
        PARAMETERS = {
            IMCParameter(
                ParameterIdentifier.DATA_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.DATA_ALGORITHM,
            ),
            IMCParameter(
                ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.ADDRESS_ALGORITHM,
            ),
        }

    @dataclass
    class Burster(Base):
        type = PatternType.DATA_AND_ADDRESS
        NAME: str = "BURSTER"
        PARAMETERS = {
            IMCParameter(
                ParameterIdentifier.DATA_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.DATA_ALGORITHM,
            ),
            IMCParameter(
                ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.ADDRESS_ALGORITHM,
            ),
            IMCParameter(ParameterIdentifier.DATA_BURSTS, True, str),
            IMCParameter(ParameterIdentifier.SAME_ADDRESS, False, str),
        }

    @dataclass
    class Blackbird(Base):
        type = PatternType.DATA_AND_ADDRESS
        NAME: str = "BLACKBIRD"
        PARAMETERS = {
            IMCParameter(
                ParameterIdentifier.DATA_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.DATA_ALGORITHM,
            ),
            IMCParameter(
                ParameterIdentifier.ADDRESS_ALGORITHM_TYPE,
                True,
                IMCAlgorithm,
                ParameterName.ADDRESS_ALGORITHM,
            ),
        }


# IMC Memory classes
class IMCMemory:
    """All supported memory types and allocation types.
    Every specialized memory block/group is derived from a base one,
    which contains common parameters all types have.
    The parameters each memory block/group supports is defined inside the
    'PARAMETERS' set, of 'IMCParameter' type."""

    @dataclass
    class Base:
        type: MemoryType
        NAME = "UNKNOWN_MEMORY_TYPE_NAME"
        _target_path: str = field(init=False)
        _physical_address_high: str = field(init=False)
        _physical_address_low: str = field(init=False)
        _physical_address: str = field(init=False)
        _enable_read_mapping: str = field(init=False)
        _enable_write_mapping: str = field(init=False)
        _enable_exec_mapping: str = field(init=False)
        _allow_aliasing: str = field(init=False)
        _mapping_mode: str = field(init=False)
        _memory_size: str = field(init=False)
        _memory_allocator_type: str = field(init=False)
        _base_parameters: set = field(default_factory=lambda: set())

        PARAMETERS = {}

        @classmethod
        def getTypes(cls):
            """Get all specialized memory block subclasses.
            :return: List of specialized memory blocks."""
            return cls.__subclasses__()

        @classmethod
        def getSubclassByName(cls, name):
            """Helper function to get an specialized memory block by it's name.
            :param name: name of the memory block allocator.
            :return: the specialized memory block subclass.
            If not found returns None"""
            for subclass in cls.__subclasses__():
                if subclass.NAME == name:
                    return subclass
            return None

        def __post_init__(self):
            """Defines the identifier of type-dependant parameters.
            Runs after initialization, when a type has been provided.
            Merges base parameters with specialized ones."""
            if self.type == MemoryType.BLOCK:
                self._memory_allocator_type = (
                    ParameterName.MEMORY_ALLOCATOR_TYPE
                )
                self._memory_size = ParameterIdentifier.MEMORY_SIZE_IN_BYTES
                self._mapping_mode = (
                    ParameterIdentifier.MEMORY_BLOCK_MAPPING_MODE
                )
                self._allow_aliasing = (
                    ParameterIdentifier.MEMORY_BLOCK_ALLOW_ALIASING
                )
                self._enable_exec_mapping = (
                    ParameterIdentifier.MEMORY_BLOCK_ENABLE_EXEC_MAPPING
                )
                self._enable_read_mapping = (
                    ParameterIdentifier.MEMORY_BLOCK_ENABLE_READ_MAPPING
                )
                self._enable_write_mapping = (
                    ParameterIdentifier.MEMORY_BLOCK_ENABLE_WRITE_MAPPING
                )
                self._physical_address = (
                    ParameterIdentifier.MEMORY_BLOCK_PHYSICAL_ADDRESS
                )
                self._physical_address_low = (
                    ParameterIdentifier.MEMORY_BLOCK_PHYSICAL_ADDRESS_LOW
                )
                self._physical_address_high = (
                    ParameterIdentifier.MEMORY_BLOCK_PHYSICAL_ADDRESS_HIGH
                )
                self._target_path = ParameterIdentifier.MEMORY_BLOCK_TARGET_PATH

            elif self.type == MemoryType.GROUP:
                self._memory_allocator_type = (
                    ParameterIdentifier.MEMORY_GROUP_BLOCK_TYPE
                )
                self._memory_size = (
                    ParameterIdentifier.MEMORY_GROUP_SIZE_IN_BYTES
                )
                self._mapping_mode = (
                    ParameterIdentifier.MEMORY_GROUP_MAPPING_MODE
                )
                self._allow_aliasing = (
                    ParameterIdentifier.MEMORY_GROUP_ALLOW_ALIASING
                )
                self._enable_exec_mapping = (
                    ParameterIdentifier.MEMORY_GROUP_ENABLE_EXEC_MAPPING
                )
                self._enable_read_mapping = (
                    ParameterIdentifier.MEMORY_GROUP_ENABLE_READ_MAPPING
                )
                self._enable_write_mapping = (
                    ParameterIdentifier.MEMORY_GROUP_ENABLE_WRITE_MAPPING
                )
                self._physical_address = (
                    ParameterIdentifier.MEMORY_GROUP_PHYSICAL_ADDRESS
                )
                self._physical_address_low = (
                    ParameterIdentifier.MEMORY_GROUP_PHYSICAL_ADDRESS_LOW
                )
                self._physical_address_high = (
                    ParameterIdentifier.MEMORY_GROUP_PHYSICAL_ADDRESS_HIGH
                )
                self._target_path = ParameterIdentifier.MEMORY_GROUP_TARGET_PATH
                group_base_parameters = {
                    IMCParameter(
                        ParameterIdentifier.MEMORY_GROUP_OVERALL,
                        True,
                        str,
                        ParameterName.MEMORY_BLOCK_GROUP_OVERALL,
                    ),
                }
                self._base_parameters = self._base_parameters.union(
                    group_base_parameters
                )

            self._base_parameters = self._base_parameters.union(
                {
                    IMCParameter(
                        self._memory_allocator_type,
                        True,
                        str,
                        ParameterName.MEMORY_ALLOCATOR_TYPE,
                    ),
                    IMCParameter(
                        self._memory_size, True, int, ParameterName.MEMORY_SIZE
                    ),
                }
            )
            self.init_parameters()
            self.PARAMETERS = self._base_parameters.union(self.PARAMETERS)

    @dataclass
    class Malloc(Base):
        NAME: str = "MALLOC"

        def init_parameters(self):
            pass

    @dataclass
    class SVOS(Base):
        NAME: str = "SVOS"

        def init_parameters(self):
            self.PARAMETERS = {
                IMCParameter(
                    self._mapping_mode,
                    False,
                    IMCMappingMode,
                    ParameterName.MEMORY_MAPPING_MODE,
                ),
                IMCParameter(
                    self._target_path, False, str, ParameterName.TARGET_PATH
                ),
                IMCParameter(
                    self._physical_address_high,
                    False,
                    int,
                    ParameterName.PHYSICAL_ADDRESS_HIGH,
                ),
                IMCParameter(
                    self._physical_address_low,
                    False,
                    int,
                    ParameterName.PHYSICAL_ADDRESS_LOW,
                ),
                IMCParameter(
                    self._physical_address,
                    False,
                    int,
                    ParameterName.PHYSICAL_ADDRESS,
                ),
                IMCParameter(
                    self._enable_read_mapping,
                    False,
                    bool,
                    ParameterName.ENABLE_READ_MAPPING,
                ),
                IMCParameter(
                    self._enable_write_mapping,
                    False,
                    bool,
                    ParameterName.ENABLE_WRITE_MAPPING,
                ),
                IMCParameter(
                    self._enable_exec_mapping,
                    False,
                    bool,
                    ParameterName.ENABLE_EXEC_MAPPING,
                ),
                IMCParameter(
                    self._allow_aliasing,
                    False,
                    bool,
                    ParameterName.ALLOW_ALIASING,
                ),
            }
