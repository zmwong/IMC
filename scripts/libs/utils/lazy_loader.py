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
This module allows for the lazy loading of modules and classes to reduce
memory usage by loading only the necessary definitions when they are needed.

The `LazyLoader` class provides a static method for dynamically loading
modules or classes at runtime, which can improve performance and reduce
startup time for large applications.
"""

import importlib.util
import sys


class LazyLoader:
    """
    A utility class for lazy loading modules and classes.

    The `LazyLoader` class provides a static method `load` that allows for
    dynamically loading a module or a specific class from a module at runtime.
    This can be useful for reducing memory usage and improving performance
    by delaying the loading of unused modules or classes.

    Methods:
        load(module_name, class_name=None): Loads a module or a specific class
            from a module dynamically.
    """

    @staticmethod
    def load(module_name, class_name=None):
        """
        Dynamically loads a module or a specific class from a module.

        This method checks if the module is already loaded in `sys.modules`.
        If not, it uses the `importlib.util` module to find and load the module.
        If a class name is provided, it retrieves the class from the loaded module.

        Args:
            module_name (str): The package path of the module to load.
            class_name (str, optional): The name of the class to retrieve from
                the module. Defaults to `None`.

        Returns:
            object: The loaded module or the specified class from the module.

        Raises:
            ImportError: If the module cannot be found or if the specified class
                does not exist in the module.

        Example:
            To load a module:
            ```
            module = LazyLoader.load("os")
            print(module.name)  # Output: "os"
            ```

            To load a specific class from a module:
            ```
            MyClass = LazyLoader.load("my_package.my_module", "MyClass")
            instance = MyClass()
            ```
        """
        # Check if the module is already in sys.modules
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            # Find the module specification based on the module name
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                raise ImportError(f"No module named '{module_name}'")

            # Use the LazyLoader to delay the module loading
            loader = importlib.util.LazyLoader(spec.loader)
            spec.loader = loader

            # Create a new module based on the spec and add it to sys.modules
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module

            # Execute the module with the lazy loader
            loader.exec_module(module)

        # If a class name is provided, return that class from the module
        if class_name:
            try:
                return getattr(module, class_name)
            except AttributeError:
                raise ImportError(
                    f"Module '{module_name}' does not have a class named '{class_name}'"
                )

        # Otherwise, return the whole module
        return module
