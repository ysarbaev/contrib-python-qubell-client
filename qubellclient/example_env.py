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

""" Example shows how to configure environment from scratch """

from qubellclient.private.platform import QubellPlatform, Context


# New organization needs environment to be set up
context = Context(user="tester@qubell.com", password="password", api="http://api.qubell.com")
# Initialize our qubell platform
platform = QubellPlatform(context=context)
# Try to login
if not platform.authenticate():
    print("Wrong credentials")
    exit(1)

# Create organization
org = platform.organization(name="test-org")

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

# Add cloud provider account
access = {
  "provider": "aws-ec2",
  "usedEnvironments": [],
  "ec2SecurityGroup": "default",
  "providerCopy": "aws-ec2",
  "name": "test-provider",
  "jcloudsIdentity": "AAAAAA",
  "jcloudsCredential": "AAAAAA",
  "jcloudsRegions": "us-east-1"
}
prov = org.provider(access)
env.providerAdd(prov)

print "Organization %s ready"