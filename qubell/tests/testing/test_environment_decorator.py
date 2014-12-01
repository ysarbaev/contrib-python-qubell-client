import unittest
from qubell.api.testing import environment
__author__ = 'dmakhno'


class DummyTests(object):
    applications = []
    def test_nothing(self): pass
    def test_fail(self): assert False
    def helper(self): pass
    @staticmethod
    def test_manager(): pass
    @classmethod
    def test_factory(cls): pass


class EnvironmentDecoratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_tests = ["test_nothing", "test_fail"]
        cls.clazz = environment({"a":{"A":"AA"}, "b":{"B":"BB"}, "default":{"C":"CC"}})(DummyTests)


    def test_patch_multiplication_test_test_methods(self):
        new_classes = ['DummyTests_a', 'DummyTests_b', 'DummyTests']
        new_tests = ['test_factory',
                     'test_fail',
                     'test_manager',
                     'test_nothing',]


        for name in new_tests:
            assert name in self.clazz.__dict__

        for case in new_classes:
            assert case in globals()
            for test in new_tests:
                assert test in globals()[case].__dict__



