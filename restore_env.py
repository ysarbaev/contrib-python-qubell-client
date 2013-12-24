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
import yaml
from qubell.api.private.platform import QubellPlatform, Auth




"""
Example shows how to configure environment from scratch.
To use this script, setup environmnt variables or modify defauls (see bellow) 

Environment variables:
QUBELL_USER, QUBELL_PASSWORD - user to access qubell
QUBELL_API - url to qubell platform
QUBELL_ORG - name of organization to use. Will be created if not exists.

PROVIDER, REGION, JCLOUDS_IDENTITY, JCLOUDS_CREDENTIALS - credentials for amazon ec2. (will create provider)


To run script, set up environment variables and run script by:

python create_env.py

"""

user = os.environ.get('QUBELL_USER', 'user')
password = os.environ.get('QUBELL_PASSWORD', 'password')
api = os.environ.get('QUBELL_API', 'https://express.qubell.com')
org = os.environ.get('QUBELL_ORG', 'organization')
zone = os.environ.get('QUBELL_ZONE','')

provider = os.environ.get('PROVIDER', 'aws-ec2')
region = os.environ.get('REGION', 'us-east-1')
identity = os.environ.get('JCLOUDS_IDENTITY')
credentials = os.environ.get('JCLOUDS_CREDENTIALS')


__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__version__ = "1.0.6"
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

# Qubell access info
auth = Auth(user=user, password=password, tenant=api)
env_path=os.path.join(os.path.dirname(__file__), 'env-for-tests.yml')
env_file=open(env_path)
cfg = yaml.load(env_file)

# Get cloud access info
cfg['organizations'][0].update({'providers': [cloud_access]})
cfg['organizations'][0].update({'name':org})

platform = QubellPlatform(auth=auth)

assert platform.authenticate()
print "Authorization passed"

platform.restore(cfg)
print "Restore finished"


