#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of using all_patched_cursors feature

This example demonstrates how to use the all_patched_cursors class attribute
to automatically apply the PatchNewCursors decorator to all test methods.
"""
import unittest
from destral.testing import OOTestCase
from destral.patch import PatchNewCursors


class ExampleWithoutPatching(OOTestCase):
    """
    Example test class without cursor patching.
    
    Use this when your tests don't create new cursors internally.
    """
    all_patched_cursors = False  # This is the default
    
    def test_simple_operation(self):
        """Test a simple operation without cursor creation"""
        # Your test logic here
        self.assertTrue(True)


class ExampleWithManualPatching(OOTestCase):
    """
    Example test class with manual cursor patching per method.
    
    Use this when only some test methods need cursor patching.
    """
    
    def test_without_patching(self):
        """This test doesn't need cursor patching"""
        self.assertTrue(True)
    
    @PatchNewCursors()
    def test_with_patching(self):
        """This test needs cursor patching (manually decorated)"""
        # If your code creates new cursors with sql_db.db_connect(),
        # they will all point to the same transaction cursor
        self.assertTrue(True)


class ExampleWithAutomaticPatching(OOTestCase):
    """
    Example test class with automatic cursor patching for all methods.
    
    Use this when ALL test methods need cursor patching.
    This is cleaner than decorating each method manually.
    """
    all_patched_cursors = True  # Enable automatic patching
    
    def test_method_one(self):
        """Automatically decorated with PatchNewCursors"""
        # All cursors created internally will use the transaction cursor
        self.assertTrue(True)
    
    def test_method_two(self):
        """Also automatically decorated with PatchNewCursors"""
        # No need to add @PatchNewCursors() decorator manually
        self.assertTrue(True)
    
    def helper_method(self):
        """Helper methods (not starting with 'test') are not decorated"""
        return "This is not decorated"
    
    @classmethod
    def class_helper(cls):
        """Class methods are not decorated"""
        return "This is a class method"
    
    @staticmethod
    def static_helper():
        """Static methods are not decorated"""
        return "This is a static method"


if __name__ == '__main__':
    unittest.main()
