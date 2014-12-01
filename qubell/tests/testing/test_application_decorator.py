# Copyright (c) 2013 Qubell Inc., http://qubell.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Vasyl Khomenko"
__email__ = "vkhomenko@qubell.com"
__copyright__ = "Copyright 2014, Qubell.com"
__license__ = "Apache"

import unittest
from qubell.api.private.testing import environment, applications


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
        new_tests = [ 'test01_launch_test1',
                     'test01_launch_test2',
                     'test_factory',
                     'test_fail',
                     'test_manager',
                     'test_nothing',
                     'testzy_destroy_test1',
                     'testzy_destroy_test2']
        for name in new_tests:
            assert name in self.clazz.__dict__

