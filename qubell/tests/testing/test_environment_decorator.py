import unittest
from qubell.api.private.testing import environment, applications

__author__ = 'dmakhno'

class DummyTests(object):
    #environment = None
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
        cls.env_names = ["a_for_DummyTests", "b_for_DummyTests"]
        cls.clazz = environment({"a":{"A":"AA"}, "b":{"B":"BB"}, "default":{"C":"CC"}})(DummyTests)

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



class ApplicationDecoratorTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        def mocktest(*args, **kwargs):
            pass
        cls._launch_instance = mocktest
        cls.old_tests = ["test_nothing", "test_fail"]
        cls.appdata = ([{'name':'test1'}, {'name':'test2'}])
        cls.clazz = applications(cls.appdata)(DummyTests)


    def test_application_decorator(self):
        new_tests = ["test01_launch_test1", # Here instances should be launched
                     "test01_launch_test2",
                     "test_nothing",
                     "test_manager",
                     "test_fail"]
        for name in new_tests:
            assert name in self.clazz.__dict__

