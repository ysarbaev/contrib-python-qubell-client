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

    @classmethod
    def setUpClass(cls):
        cls.old_tests = ["test_nothing", "test_fail"]
        cls.env_names = ["a_for_DummyTests", "b_for_DummyTests"]
        cls.clazz = environment({"a":{"A":"AA"}, "b":{"B":"BB"}, "default":{"C":"CC"}})(cls.DummyTests)

    def test_patch_multiplication_test_test_methods(self):
        new_tests = ["test_nothing_on_environment_a_for_DummyTests",
                     "test_nothing_on_environment_b_for_DummyTests",
                     "test_nothing_on_environment_default",
                     "test_fail_on_environment_a_for_DummyTests",
                     "test_fail_on_environment_b_for_DummyTests",
                     "test_fail_on_environment_default"]
        for name in self.old_tests:
            assert name not in self.clazz.__dict__
        for name in new_tests:
            assert name in self.clazz.__dict__

    def test_environment_name_in_test_name(self):
        for name in self.env_names:
            assert name in [x['name'] for x in self.clazz.environments]

    def test_patch_environment_names_with_test_scope_leave_default_name_unchanged(self):
        assert "default" in [x['name'] for x in self.clazz.environments]

