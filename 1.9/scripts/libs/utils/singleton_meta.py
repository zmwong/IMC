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

"""
This module contains the definition for the `SingletonMeta` metaclass.

The `SingletonMeta` metaclass ensures that a class has only one instance and provides
a global point of access to that instance. It is commonly used to implement the Singleton
design pattern.
"""


class SingletonMeta(type):
    """
    A metaclass for implementing the Singleton design pattern.

    The `SingletonMeta` metaclass ensures that a class has only one instance. If the class
    is instantiated multiple times, the same instance is returned. This is achieved by
    storing instances in a dictionary, where the class itself is the key.

    Note:
        The Singleton behavior depends on the import path of the class. If the same class
        is imported using different paths, it will be treated as a different class, and
        multiple instances may be created.

    Attributes:
        _instances (dict): A dictionary to store instances of classes using this metaclass.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Controls the instantiation of classes using the `SingletonMeta` metaclass.

        If an instance of the class does not already exist, it creates a new instance
        and stores it in the `_instances` dictionary. If an instance already exists,
        it returns the existing instance.

        Args:
            *args: Positional arguments to pass to the class constructor.
            **kwargs: Keyword arguments to pass to the class constructor.

        Returns:
            object: The singleton instance of the class.

        Example:
            ```
            class MyClass(metaclass=SingletonMeta):
                pass

            obj1 = MyClass()
            obj2 = MyClass()
            assert obj1 is obj2  # Both variables point to the same instance
            ```
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
