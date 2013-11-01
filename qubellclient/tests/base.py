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
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__version__ = "1.0.1"
__email__ = "vkhomenko@qubell.com"

import testtools
import nose.plugins.attrib
from qubellclient.private.platform import QubellPlatform, Context
from qubellclient.private.manifest import Manifest
import os
from qubellclient.tools import rand
import logging as log


user = os.environ.get('QUBELL_USER')
password = os.environ.get('QUBELL_PASSWORD')
api = os.environ.get('QUBELL_API')
org = os.environ.get('QUBELL_ORG')

if not user: log.error('No username provided. Set QUBELL_USER env')
if not password: log.error('No password provided. Set QUBELL_PASSWORD env')
if not api: log.error('No api url provided. Set QUBELL_API env')


def attr(*args, **kwargs):
    """A decorator which applies the nose and testtools attr decorator
    """
    def decorator(f):
        f = testtools.testcase.attr(args)(f)
        if not 'skip' in args:
            return nose.plugins.attrib.attr(*args, **kwargs)(f)
        # TODO: Should do something if test is skipped
    return decorator

class BaseTestCasePrivate(testtools.TestCase):
    ## TODO: Main preparation should be here
    """ Here we prepare global env. (load config, etc)
    """

    @classmethod
    def setUpClass(cls):
        cls.prefix = rand()
        cls.context = Context(user=user, password=password, api=api)

    # Initialize platform and check access
        cls.platform = QubellPlatform(context=cls.context)
        assert cls.platform.authenticate()

    # Set default manifest for app creation
        cls.manifest = Manifest(file=os.path.join(os.path.dirname(__file__), 'default.yml'), name='BaseTestManifest')

    # Initialize organization
        if org:
            cls.organization = cls.platform.organization(name=org)
        else:
            cls.organization = cls.platform.organization(name='test-frame1work-run')

    # Initialize environment
        cls.environment = cls.organization.environment(name='default')


    @classmethod
    def tearDownClass(cls):
        print "BaseTestCasePrivate TeadDownClass"

    def setUp(self):
    # Run before each test
        super(BaseTestCasePrivate, self).setUp()
        pass

    def tearDown(self):
    # Run after each test
        super(BaseTestCasePrivate, self).tearDown()
        pass
