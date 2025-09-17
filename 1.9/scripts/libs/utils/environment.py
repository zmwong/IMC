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
"""
Helps to get system environment information such as OS, support of avx512 opcode
and pinnedmem, devmem.
"""
from dataclasses import dataclass, field
import platform
import os
from scripts.libs.definitions.paths import DefaultPaths
from scripts.libs.definitions.imc import BinaryNames, PyFrameworkExecutables
from scripts.libs.utils.paths import fix_full_path_from_root


@dataclass
class EnvironmentInfo:
    _imc_path: str = field(init=False)
    _imc_runner_path: str = field(init=False)
    _avx512_support: bool = False
    _devmem_support: bool = False
    _nix = False

    @property
    def imc_path(self):
        return self._imc_path

    @property
    def imc_runner_path(self):
        return self._imc_runner_path

    @property
    def avx512_support(self):
        return self._avx512_support

    @property
    def devmem_support(self):
        return self._devmem_support

    @property
    def OS(self):
        return self._OS

    def get_imc_environment(self):
        """
        Provides a dictionary with all IMC-related environment information.

        Returns:
            dict: Dictionary containing IMC paths, OS info, and hardware support information
        """
        return {
            "imc_path": self._imc_path,
            "imc_runner_path": self._imc_runner_path,
            "os": self._OS,
            "avx512_support": self._avx512_support,
            "devmem_support": self._devmem_support,
            "nix": self._nix,
        }

    def get_os():
        if platform.system() == "Windows":
            return "WINDOWS"
        elif platform.system() == "Linux":
            # Check if SVOS
            if os.path.exists("/etc/svos"):
                return "SVOS"
            else:
                return "LINUX"

    _OS: str = field(default_factory=get_os)

    def is_cpu_feature_enabled(feature):
        """Check for CPU features
        :return: bool
        """
        file_info = "/proc/cpuinfo"
        read_lines = []

        try:
            with open(file_info, "r") as file:
                read_lines = file.read().splitlines()
        except (FileNotFoundError, OSError):
            # file not found or could not be read by current user
            pass
        for line in read_lines:
            if line.startswith("flags"):
                for flags in line.split(" "):
                    if flags == feature:
                        return True
        return False

    def is_avx512f_available(self):
        return EnvironmentInfo.is_cpu_feature_enabled("avx512f")

    def is_avx512f_available_on_windows(self):
        import ctypes

        return ctypes.windll.kernel32.IsProcessorFeaturePresent(7) == 1

    def is_pinned_mem_available(self):
        return os.path.exists("/usr/lib/libpmal_shared.so")

    def is_devmem_kernel_enabled(self):
        release = os.uname().release
        config_path = "/boot/config-" + release
        if not os.path.exists(config_path):
            return False
        with open(config_path) as config_file:
            for line in config_file:
                if line.strip() == "CONFIG_STRICT_DEVMEM=y":
                    return False
                else:
                    return True

    def is_devmem_bootloader_enabled(self):
        try:
            with open("/proc/cmdline") as f:
                cmdline = f.read().strip()
                if "devmem=1" in cmdline:
                    return True
                elif "devmem=0" in cmdline:
                    return False
        except IOError:
            return False

    def __post_init__(self):
        if self._OS in ["LINUX", "SVOS"]:
            self._nix = True
        if self._nix:
            default_compiled_bin = fix_full_path_from_root(
                DefaultPaths.COMPILED_TOOL_BINARY + BinaryNames.REGULAR_BINARY
            )

            default_installed_bin = (
                DefaultPaths.INSTALLED_DPKG + BinaryNames.DEBIAN_PACKAGE_BINARY
            )
            # get imc_binary
            if os.path.exists(default_installed_bin):
                self._imc_path = default_installed_bin
            elif os.path.exists(default_compiled_bin):
                self._imc_path = default_compiled_bin
            else:
                self._imc_path = None

            # set imc runner path
            default_repo_runner = fix_full_path_from_root(
                "/" + PyFrameworkExecutables.IMC_RUNNER
            )

            default_installed_runner = fix_full_path_from_root(
                DefaultPaths.INSTALLED_DPKG + PyFrameworkExecutables.IMC_RUNNER
            )

            # find the runner path
            if os.path.exists(default_installed_runner):
                self._imc_runner_path = default_installed_runner
            elif os.path.exists(default_repo_runner):
                self._imc_runner_path = default_repo_runner
            else:
                self._imc_runner_path = None

            # check avx512 support
            self._avx512_support = self.is_avx512f_available()

            # check devmem support
            if self._OS == "LINUX":
                self._devmem_support = (
                    self.is_devmem_bootloader_enabled()
                    or self.is_devmem_kernel_enabled()
                )
        elif self._OS == "WINDOWS":
            # get imc_binary
            default_bin = fix_full_path_from_root(
                "/" + BinaryNames.WINDOWS_BINARY
            )

            if os.path.exists(default_bin):
                self._imc_path = default_bin
            else:
                self._imc_path = None

            # set imc runner path
            default_repo_runner = fix_full_path_from_root(
                "/" + PyFrameworkExecutables.IMC_RUNNER
            )

            # find the runner path
            if os.path.exists(default_repo_runner):
                self._imc_runner_path = default_repo_runner
            else:
                self._imc_runner_path = None

            # check avx512 support
            self._avx512_support = self.is_avx512f_available_on_windows()
