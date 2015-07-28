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

class SetupOnce(object):
    """
    Trait for unittest.TestCase
    Allows do not use test class methods, such as setUpClass or tearDownClass.

    This allows to avoid failed suites. And always each test has failed.
    """

    __counter = 0

    setup_error = None

    def setup_once(self):
        """
        Hook method for setting up fixture before running tests.
        Has instance scope.
        """

    def teardown_once(self):
        """
        Hook method for deconstructing the test fixture after testing it.
        Has instance scope.
        """

    def setUp(self):
        super(SetupOnce, self).setUp()
        if self.__counter == 0:
            self.__counter += 1
            try:
                self.setup_once()
            except BaseException as e:
                import sys
                self.setup_error = sys.exc_info()

        if self.setup_error:
            raise self.setup_error[1], None, self.setup_error[2]

    def tearDown(self):
        if self.__counter > 1:
            self.__counter -= 1
        else:
            self.teardown_once()
        super(SetupOnce, self).tearDown()