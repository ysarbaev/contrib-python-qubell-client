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



user = os.environ['QUBELL_USER']
password = os.environ['QUBELL_PASSWORD']
api = os.environ['QUBELL_API']
org = os.environ['QUBELL_ORG']

context = Context(user=user, password=password, api=api)


if os.environ.has_key('PROVIDER'):
    provider = os.environ['PROVIDER']
else:
    provider = 'aws-ec2'
if os.environ.has_key('REGION'):
    region = os.environ['REGION']
else:
    region = 'us-east-1'
if os.environ.has_key('JCLOUDS_IDENTITY'):
    identity = os.environ['JCLOUDS_IDENTITY']
if os.environ.has_key('JCLOUDS_CREDENTIALS'):
    credentials = os.environ['JCLOUDS_CREDENTIALS']

cloud_access = {
      "provider": provider,
      "usedEnvironments": [],
      "ec2SecurityGroup": "default",
      "providerCopy": provider,
      "name": "generated-provider-for-tests",
      "jcloudsIdentity": identity,
      "jcloudsCredential": credentials,
      "jcloudsRegions": region
    }


def create_env(org):

    # Add services
    key_service = org.service(type='builtin:cobalt_secure_store', name='Keystore')
    wf_service = org.service(type='builtin:workflow_service', name='Workflow', parameters='{}')

    # Add services to environment
    env = org.environment(name = 'default')
    env.serviceAdd(key_service)
    env.serviceAdd(wf_service)
    env.policyAdd(
        {"action": "provisionVms",
         "parameter": "publicKeyId",
         "value": key_service.regenerate()['id']})

    prov = org.provider(cloud_access)
    env.providerAdd(prov)


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

        # Here defined test app via public api
        cls.manifest = Manifest(file=os.path.join(os.path.dirname(__file__), 'default.yml'), name='BaseTestManifest')
        cls.context = context

        cls.platform = QubellPlatform(context=cls.context)
        assert cls.platform.authenticate()

        cls.organization = cls.platform.organization(id=org)
#        cls.application = cls.organization.application(id='52557751e4b03292d197d05e', manifest=cls.manifest, name='BaseTestApp')

        cls.environment = cls.organization.environment()
        #create_env(cls.organization) # TODO: find proper place for this operation

    @classmethod
    def tearDownClass(cls):
        # Clean after tests here
        pass

    def setUp(self):
        super(BaseTestCasePrivate, self).setUp()
        pass

    def tearDown(self):
        super(BaseTestCasePrivate, self).tearDown()
        pass

