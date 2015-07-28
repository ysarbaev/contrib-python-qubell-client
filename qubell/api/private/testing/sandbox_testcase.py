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

import logging as log
import os
import re
import unittest
from qubell.api.globals import *
from qubell.api.private.exceptions import NotFoundError
from qubell.api.private.service import *
from qubell.api.private.testing import SandBox
from qubell.api.private.testing.setup_once import SetupOnce

class BaseTestCase(SetupOnce, unittest.TestCase):
    platform = None
    parameters = None
    sandbox = None
    environments = None
    applications = []
    instances = []
    current_environment = DEFAULT_ENV_NAME()

    setup_error = None
    setup_error_trace = None
    setup_skip = None

    @classmethod
    def environment(cls, organization):
        provider_config = PROVIDER_CONFIG

        # Old style components tests declared name as 'test-provider'. Now we cannot add this provider to env where another provider set.
        if (cls.parameters['provider_name']=='test-provider') or (not(cls.parameters['provider_name'])):
            prov = PROVIDER['provider_name']
        else:
            prov = cls.parameters['provider_name']

        # Default add-on for every env
        addon = {"services":
                    [{"name": DEFAULT_CREDENTIAL_SERVICE()},
                     {"name": DEFAULT_WORKFLOW_SERVICE()},
                     {"name": prov}
                    ]}

        servs = [{"type": COBALT_SECURE_STORE_TYPE, "name": DEFAULT_CREDENTIAL_SERVICE()},
                 {"type": WORKFLOW_SERVICE_TYPE, "name": DEFAULT_WORKFLOW_SERVICE()},
                 {"type": CLOUD_ACCOUNT_TYPE, "name": prov, "parameters": provider_config}]

        insts = []

        # Add provider, keystore, workflow to every env.
        envs = cls.environments or [{"name": DEFAULT_ENV_NAME()},]
        for env in envs:
            env.update(addon)

        return {
            "organization": {"name": organization},
            "services": servs,
            "instances": insts,
            "environments": envs,
            "applications": cls.applications}

    @classmethod
    def timeout(cls):
        return 15

    def setup_once(cls):
        super(BaseTestCase, cls).setup_once()

        log.info("\n\n\n---------------  Preparing sandbox...  ---------------")
        try:
            cls.service_instances = []
            cls.regular_instances = []
            org = cls.parameters.get('organization') or getattr(cls, 'source_name', False) or cls.__class__.__name__

            cls.sandbox = SandBox(cls.platform, cls.environment(org))
            cls.organization = cls.sandbox.make()

            if cls.__dict__.get('platform_version'):
                ver = cls.organization.get_default_environment().get_backend_version()
                try:
                    current_version = float(ver)
                except ValueError:
                    # dev version: '41.0.148.g5ef3b00 2015-05-14 14:49:36'
                    # universe version: 'v. v41.0.171.g8230c89'
                    current_version = float(re.findall(r'\d+', ver)[0]+'.'+re.findall(r'\d+', ver)[1])
                required_version = float(cls.platform_version)
                if current_version < required_version:
                    cls.setup_skip = 'Platform version %s required, got %s' % (required_version, current_version)

            ### Start ###

            if cls.setup_error or cls.setup_skip:
                pass # go to exit
            else:
                # If 'meta' in sandbox, restore applications that comes in meta before.
                if cls.__dict__.get('meta'):
                    cls.upload_metadata_applications(cls.__dict__.get('meta'))

                services_to_start = [x for x in cls.sandbox['applications'] if x.get('add_as_service', False)]
                instances_to_start = [x for x in cls.sandbox['applications'] if x.get('launch', True) and not x.get('add_as_service', False)]

                for appdata in services_to_start:
                    ins = cls.launch_instance(appdata)
                    cls.service_instances.append(ins)
                    cls.organization.environments[cls.current_environment].add_service(ins)
                cls.check_instances(cls.service_instances)

                for appdata in instances_to_start:
                    cls.regular_instances.append(cls.launch_instance(appdata))
                cls.check_instances(cls.regular_instances)

        except BaseException as e:
            import traceback
            cls.setup_error_trace = traceback.format_exc()
            log.critical(e)
            log.critical(cls.setup_error_trace)
        log.info("\n---------------  Sandbox prepared  ---------------\n\n")

    def teardown_once(cls):
        log.info("\n---------------  Cleaning sandbox  ---------------")

        cls.destroy_instances(cls.regular_instances)
        cls.destroy_instances(cls.service_instances)
        cls.regular_instances = []
        cls.service_instances = []

        log.info("\n---------------  Sandbox cleaned  ---------------\n")
        super(BaseTestCase, cls).tearDownClass()

    def setUp(self):
        super(BaseTestCase, self).setUp()
        if self.setup_skip:
            raise self.skipTest(self.setup_skip)


    @classmethod
    def upload_metadata_applications(cls, metadata):
        cls.organization.set_applications_from_meta(metadata)

    def launch_instance(cls, appdata):
        application = cls.organization.applications[appdata['name']]
        environment = cls.organization.environments[cls.current_environment]
        instance = cls.organization.create_instance(application=application,
                                                    environment=environment,
                                                    parameters=appdata.get('parameters', {}),
                                                    **appdata.get('settings',{}))
        return instance

    @classmethod
    def check_instances(cls, instances):
        for instance in instances:
            if not instance.running(timeout=cls.timeout()):
                if instance.error: # If error message exists - status should be error, else instance faced timeout
                    error = instance.error.strip()
                else:
                    error = 'Instance status: %s after timeout %s' % (instance.status, cls.timeout())

                # TODO: if instance fails to start during tests, add proper unittest log
                if os.getenv("QUBELL_DEBUG", None) and not('false' in os.getenv("QUBELL_DEBUG", None)):
                    pass

                assert False, "Instance %s (%s): %s" % (instance.name, instance.instanceId, error)

    @classmethod
    def destroy_instances(cls, instances):
        if os.getenv("QUBELL_DEBUG", None) and not('false' in os.getenv("QUBELL_DEBUG", None)):
            log.info("QUBELL_DEBUG is ON\n DO NOT clean sandbox")
        else:
            for instance in instances:
                instance.destroy()
                if not instance.destroyed(cls.timeout()):
                    log.error("Instance {0} ({1}) was not destroyed properly. Org: {2}, App: {3} ".format(instance.id,
                                                                                                          instance.name,
                                                                                                          instance.organizationId,
                                                                                                          instance.applicationId))

    def find_by_application_name(self, name):
        for inst in self.regular_instances+self.service_instances:
            if inst.application.name == name:
                return inst
        raise NotFoundError