import unittest
from qubell.api.private.testing import environment

__author__ = 'dmakhno'
class EnvironmentDecoratorTests(unittest.TestCase):

    class DummyTests(object):
        #environment = None

        def test_nothing(self): pass
        def test_fail(self): assert False
        def helper(self): pass
        @staticmethod
        def test_manager(): pass
        @classmethod
        def test_factory(cls): pass

    def test_patch_environment_names_with_test_scope(self):
        old_tests = ["test_nothing", "test_fail"]
        new_tests = ["test_nothing_on_environment-a_for_DummyTests",
                     "test_nothing_on_environment-b_for_DummyTests",
                     "test_nothing_on_environment-default",
                     "test_fail_on_environment-a_for_DummyTests",
                     "test_fail_on_environment-b_for_DummyTests",
                     "test_fail_on_environment-default"]
        env_names = ["a_for_DummyTests", "b_for_DummyTests"]

        clazz = environment({"a":{"A":"AA"}, "b":{"B":"BB"}, "default":{"C":"CC"}})(self.DummyTests)
        for name in old_tests:
            assert name not in clazz.__dict__
        for name in new_tests:
            assert name in clazz.__dict__
        for name in env_names:
            assert name in [x['name'] for x in clazz.environments]
        assert "default" in [x['name'] for x in clazz.environments]

