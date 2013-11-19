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

import os
import sys

from qubellclient.private.platform import QubellPlatform, Context
import logging as log

user = os.environ.get('QUBELL_USER')
password = os.environ.get('QUBELL_PASSWORD')
api = os.environ.get('QUBELL_API')
org = os.environ.get('QUBELL_ORG')


provider = os.environ.get('PROVIDER', 'aws-ec2')
region = os.environ.get('REGION', 'us-east-1')
identity = os.environ.get('JCLOUDS_IDENTITY')
credentials = os.environ.get('JCLOUDS_CREDENTIALS')

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


def setUpModule():
# This runs once for module (all tests)
# Best place to initialize platform.
# Here we check existance of given credentials and create services if needed

    exit = 0
    if not user:
        log.error('No username provided. Set QUBELL_USER env')
        exit = 1
    if not password:
        log.error('No password provided. Set QUBELL_PASSWORD env')
        exit = 1
    if not api:
        log.error('No api url provided. Set QUBELL_API env')
        exit = 1

    if exit:
        sys.exit(1)

# Setup access
    context = Context(user=user, password=password, api=api)

# Initialize platform and check access
    platform = QubellPlatform(context=context)
    assert platform.authenticate()

    if os.environ.get('QUBELL_NEW'):
        create_env(platform)


def create_env(platform):

# Initialize organization
    if org: organization = platform.organization(name=org)
    else: organization = platform.organization(name='test-framework-run')

# Create independent environment
    environment = organization.environment(name='default') #TODO: create own
    environment.clean()

# Add services
    key_service = organization.service(type='builtin:cobalt_secure_store', name='Keystore')
    wf_service = organization.service(type='builtin:workflow_service', name='Workflow', parameters= {'configuration.policies': '{}'})

# Add services to environment
    environment.serviceAdd(key_service)
    environment.serviceAdd(wf_service)
    environment.policyAdd(
        {"action": "provisionVms",
         "parameter": "publicKeyId",
         "value": key_service.regenerate()['id']})
# Add cloud provider
    provider = organization.provider(name='test-provider', parameters=cloud_access)
    environment.providerAdd(provider)



def tearDownModule():
# Clean after tests executed
    pass
# Run after framework finish
# Clean after tests here
# Remove environment
    #cls.environment.delete()

# Remove created services
    #cls.key_service.delete()
    #cls.wf_service.delete()

# Remove provider
    #cls.provider.delete()
