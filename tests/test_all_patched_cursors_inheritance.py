#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test inheritance behavior with all_patched_cursors"""
import unittest
from destral.testing import OOTestCaseMeta
import six


class TestInheritance(unittest.TestCase):
    """Test that all_patched_cursors works correctly with inheritance"""
    
    def test_child_inherits_patching(self):
        """Child class should inherit all_patched_cursors from parent"""
        
        @six.add_metaclass(OOTestCaseMeta)
        class ParentClass(object):
            all_patched_cursors = True
            
            def test_parent_method(self):
                pass
        
        class ChildClass(ParentClass):
            def test_child_method(self):
                pass
        
        # Both parent and child test methods should be callable
        self.assertTrue(callable(ChildClass.test_parent_method))
        self.assertTrue(callable(ChildClass.test_child_method))
    
    def test_child_can_override_patching(self):
        """Child class can override all_patched_cursors from parent"""
        
        @six.add_metaclass(OOTestCaseMeta)
        class ParentClass(object):
            all_patched_cursors = True
            
            def test_parent_method(self):
                pass
        
        @six.add_metaclass(OOTestCaseMeta)
        class ChildClass(ParentClass):
            all_patched_cursors = False
            
            def test_child_method(self):
                pass
        
        # Child should not have patching applied
        self.assertTrue(callable(ChildClass.test_child_method))
        self.assertFalse(hasattr(ChildClass.test_child_method, '__wrapped__'))


if __name__ == '__main__':
    unittest.main()
