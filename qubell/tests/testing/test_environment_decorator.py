import unittest2
from qubell.api.private.testing import environment

__author__ = 'dmakhno'
class EnvironmentDecoratorTests(unittest2.TestCase):

    class DummyTests(object):
        #environment = None

        def test_nothing(self): pass
        def test_fail(self): assert False
        def helper(self): pass
        @staticmethod
        def test_manager(): pass
        @classmethod
        def test_factory(cls): pass

    def test_apply(self):
        old_tests = ["test_nothing", "test_fail"]
        new_tests = ["test_nothing_on_environment_a", "test_nothing_on_environment_b", "test_fail_on_environment_a", "test_fail_on_environment_b"]
        clazz = environment({"a":"A", "b":"B"})(self.DummyTests)
        for name in old_tests:
            assert name not in clazz.__dict__
        for name in new_tests:
            assert name in clazz.__dict__