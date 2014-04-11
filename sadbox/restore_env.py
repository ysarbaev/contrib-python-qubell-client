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
import sys
import yaml
from qubell.api.private.platform import QubellPlatform
import logging


"""
Example shows how to configure environment from scratch.
To use this script, setup environmnt variables or modify defauls (see bellow) 

Environment variables:
QUBELL_USER, QUBELL_PASSWORD - user to access qubell
QUBELL_TENANT - url to qubell platform
QUBELL_ORGANIZATION - name of organization to use. Will be created if not exists.

PROVIDER_TYPE, PROVIDER_REGION, PROVIDER_IDENTITY, PROVIDER_CREDENTIAL - credentials for amazon ec2. (will create provider)


To run script, set up environment variables and run script by:

python restore_env.py envfile.env
or
./restore_env.py
Will use default.env

"""

if os.getenv('QUBELL_LOG_LEVEL', 'info') == 'debug':
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)


default_env = os.path.join(os.path.dirname(__file__), 'default.env')

user = os.environ.get('QUBELL_USER', 'user')
password = os.environ.get('QUBELL_PASSWORD', 'password')
tenant = os.environ.get('QUBELL_TENANT', 'https://express.qubell.com')
org = os.environ.get('QUBELL_ORGANIZATION', None)
zone = os.environ.get('QUBELL_ZONE', '')

provider = os.environ.get('PROVIDER_TYPE', 'aws-ec2')
region = os.environ.get('PROVIDER_REGION', 'us-east-1')
identity = os.environ.get('PROVIDER_IDENTITY')
credentials = os.environ.get('PROVIDER_CREDENTIAL')


__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__email__ = "vkhomenko@qubell.com"


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


env = None
if len(sys.argv)>1:
    env = sys.argv[1]
else:
    env = default_env

env_file = open(env)
cfg = yaml.load(env_file)

# Get cloud access info
cfg['organizations'][0].update({'providers': [cloud_access]})
if org:
    cfg['organizations'][0].update({'name': org})

platform = QubellPlatform()

platform.connect(user=user, password=password, tenant=tenant)
print "Authorization passed"

import pprint
pprint.pprint(cfg)
print "Restoring env: %s" % env
platform.restore(cfg)
print "Restore finished"

