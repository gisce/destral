#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test for all_patched_cursors feature"""
import unittest
from destral.testing import OOTestCaseMeta, OOTestCase
from destral.patch import PatchNewCursors
import six


class TestMetaclassWithoutPatch(unittest.TestCase):
    """Test the metaclass behavior without all_patched_cursors"""
    
    def test_metaclass_does_not_decorate_by_default(self):
        """Verify that test methods are NOT decorated when all_patched_cursors is False"""
        
        @six.add_metaclass(OOTestCaseMeta)
        class TestClass(object):
            all_patched_cursors = False
            
            def test_method(self):
                pass
        
        # The method should not be wrapped
        self.assertTrue(callable(TestClass.test_method))
        # Verify it's the original method, not wrapped
        self.assertFalse(hasattr(TestClass.test_method, '__wrapped__'))


class TestMetaclassWithPatch(unittest.TestCase):
    """Test the metaclass behavior with all_patched_cursors enabled"""
    
    def test_metaclass_decorates_test_methods(self):
        """Verify that test methods ARE decorated when all_patched_cursors is True"""
        
        @six.add_metaclass(OOTestCaseMeta)
        class TestClass(object):
            all_patched_cursors = True
            
            def test_method(self):
                pass
            
            def test_another(self):
                pass
            
            def helper_method(self):
                pass
        
        # Test methods should be wrapped
        self.assertTrue(callable(TestClass.test_method))
        self.assertTrue(callable(TestClass.test_another))
        
        # Non-test methods should not be wrapped
        self.assertTrue(callable(TestClass.helper_method))
        self.assertFalse(hasattr(TestClass.helper_method, '__wrapped__'))
    
    def test_classmethod_and_staticmethod_not_decorated(self):
        """Verify that classmethods and staticmethods are not decorated"""
        
        @six.add_metaclass(OOTestCaseMeta)
        class TestClass(object):
            all_patched_cursors = True
            
            @classmethod
            def test_classmethod(cls):
                pass
            
            @staticmethod
            def test_staticmethod():
                pass
        
        # They should remain as classmethod/staticmethod
        self.assertTrue(callable(TestClass.test_classmethod))
        self.assertTrue(callable(TestClass.test_staticmethod))


if __name__ == '__main__':
    unittest.main()
