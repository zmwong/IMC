# ChangeLog

All notable changes to the Python Framework will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2025-07-04

### [Unreleased]
- Process halting and resuming proved succesfull on Windows platforms
- Throughput measurement through a PCM api was successfull on non virtualized unix platforms

### Added
- Tool Manager was added to detach the tool logic from the Runner itself, data handler class was changed to be an instance inside the manager, instead of its own singleton [#728](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/728)
- Instruction set identification was added for Windows through the use of Ctypes [#723](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/723).
- Added a Memory Handler instance that is able to retrieve information through the CPUINFO instruction, changed asm and cpuid classes to retrieve any information from cpuinfo, not just instruction sets [#742](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/742)

### Changed
- The logging system was reworked to provide better logs and performance [#741](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/741)
- --default option was renamed to --test_case, it now allows to select stress cases. It supports interval selection by instruction set or by name. [#756](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/756)

### Fix
- Component packages were missing on the components, data handlers, and runnables packages [#749](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/749).
- Batch executor was not working as expected as threads did not follow a sync up point before launching a new batch [#748](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/748).
- Fixed default test cases path issue on debian package [#730](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/730)
- Fixed compile IMC issue failing with newer versions of CMake [#722](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/722)

### Removed
- Deprecated the usage of EnvironmentInfo inside of the Runner [#729](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/729)



## [0.2.0] - 2025-04-11 - [#698](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/698) [#711](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/711)

### [Unreleased]
- Asyncio usage for the Runner is being tested to enhance memory capabilities, if promising it will be implemented in the release 3.0

### Added
- Signal handling capabilities for linux, supporting SIGTSTP and SIGCONT
- Added a new Signal Handler component
- Thread object definition to define behavior for queue and batch
- Default test cases supporting highest instruction set available
- Multiple tool parsing, supporting system args

### Fixed
- Lazyloader not using module cache to verify for created modules
- NUMA handler small bug when generating commands

### Changed
- Following on the architecture changes, the Runner is now capable of
    handling multiple tools parameters. For the moment only IMC is 
    supported. 
- IMC and System settings are now separated each having its own parsing
    and logger to provide more granularity in logs.
- Runners are now being launched with their own thread, providing 
    multithreading capabilites to the Runner
- Pytest was enabled instead of the tester for the runner script

## [0.1.0] - 2024-05-12 - [#698](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/698)

### Added
- Distributions are defined to handle the command generation
- Task Executors orchestrate the launch, monitor and termiation of threads
- Os Systems handle the os specifics for Windows, Linux and SVOS
- Factories handle the creation of the runners
- A lazy loading mechanism was added to reduce binary footprint
### Changed
- The Runner Architecture changed to adopt a component based composition. This
    can be thought of as "Lego Components" where the Runner is generated dynamically
    with the specific parts of code it requires to run with a certain behavior on a 
    specific platform.
