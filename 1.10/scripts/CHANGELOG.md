# ChangeLog

All notable changes to the Python Framework will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## [0.4.0] - 2025-09-05 - [#826] - https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/826

### [Unreleased]
- File based Parsing rework for IMC 
- new "no-color" parameter for homogeneus behaviour on terminals 

### Added
- Variable Stress: Dynamic sine-based stress patterns to vary memory stress levels over time [#809](https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/809)
- API Integration: runIMC can now be called as an API for programmatic execution  [#809] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/809
- Enhanced Memory Error Reporting: Per-thread error tracking and memory diagnostics file generation with detailed error
  information including error distribution across DIMMs, error counting and classification, exact memory error locations,
  and thread-specific error attribution [#794] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/794/files
- SIGTERM Signal Handling: Added signal handling on Linux to prevent early termination of IMC logs [#810] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/810/files
- EDAC Integration: IMVF can now access kernel memory errors using EDAC through standard userspace interfaces, monitoring
  kernel messages and sysfs for memory errors during execution [#794] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/794/files
- PCM Integration: Integrated Intel Performance Counter Monitor as a plugin for bandwidth monitoring with new plugin
  architecture and automated PCM integration in Debian packages [#804] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/804

### Changed
- Enhanced Logging: Memory parameter now shows percentage, byte equivalence, and per-instance distribution with proper units [#817] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/817
- Structured Log Organization: New IMC logs structure groups related files under timestamped directories [#808] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/808
- Cross-Platform Enhancements: Implemented Windows process control using NT APIs and improved SVOS memory target support [#792] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/792
- Development Improvements: Enhanced Copilot instructions, improved test coverage, and resolved CI/CD pipeline issues [#815] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/815

### Fix
- Memory Error Reporting: Fixed early execution termination preventing proper error reporting [#810] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/810/files
- IMC Error Reporting: Fixed intermittent error reporting issues in short executions [#819] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/819
- Log File Generation: Added log file generation in all verbosity levels [#784] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/784
- Format check of svosinfo output: IMVF was failing to use memory targets due to incorrect parsing [#806] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/806
- Fix to nightly gates on CI/CD: IMVF changed the report of errrors and exit codes, and CI/CD required fixes [#797] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/797
- PCM Windows Compatibility: Removed conditional PCM check preventing execution on Windows platforms [#807] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/807


### Removed
- EDAC Util Deprecation: Replaced edac-util dependency with direct dmesg access for improved reliability [#801] https://github.com/intel-innersource/frameworks.validation.memory.intelligent-memory-checker.intelligent-memory-checker/pull/801



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
