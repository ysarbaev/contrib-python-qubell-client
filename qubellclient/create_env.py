#!/usr/bin/python

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
import os
from qubellclient.private.platform import QubellPlatform, Context

__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__version__ = "1.0.1"
__email__ = "vkhomenko@qubell.com"

"""
Example shows how to configure environment from scratch.
To use this script, setup environmnt variables or modify defauls (see bellow) 
"""

user = os.environ.get('QUBELL_USER', 'user')
password = os.environ.get('QUBELL_PASSWORD', 'password')
api = os.environ.get('QUBELL_API', 'http://api.qubell.com')
org = os.environ.get('QUBELL_ORG', 'organization')

provider = os.environ.get('PROVIDER', 'aws-ec2')
region = os.environ.get('REGION', 'us-east-1')
identity = os.environ.get('JCLOUDS_IDENTITY')
credentials = os.environ.get('JCLOUDS_CREDENTIALS')

cloud_access = {
      "provider": provider,
      "usedEnvironments": [],
      "ec2SecurityGroup": "default",
      "providerCopy": provider,
      "name": "generated-provider",
      "jcloudsIdentity": identity,
      "jcloudsCredential": credentials,
      "jcloudsRegions": region
    }

# New organization needs environment to be set up
context = Context(user=user, password=password, api=api)
# Initialize our qubell platform
platform = QubellPlatform(context=context)
# Try to login
if not platform.authenticate():
    print("Wrong credentials")
    exit(1)

# Create organization
org = platform.organization(name=org)

# Add services
key_service = org.service(type='builtin:cobalt_secure_store', name='Keystore')
wf_service = org.service(type='builtin:workflow_service', name='Workflow', parameters='{}')

# Add services to environment
env = org.environment(name = 'default')
env.clean()
assert env.serviceAdd(key_service)
assert env.serviceAdd(wf_service)
assert env.policyAdd(
    {"action": "provisionVms",
     "parameter": "publicKeyId",
     "value": key_service.regenerate()['id']})

# Add cloud provider account

prov = org.provider(cloud_access)
assert env.providerAdd(prov)

print "Organization %s ready" % org.name