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

__author__ = "Anton Panasenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__version__ = "1.0.6"
__email__ = "apanasenko@qubell.com"

import unittest
import yaml
import logging as log

from functools import wraps

from qubell.api.private.instance import Instance
from qubell.api.private.manifest import Manifest


def values(names):
    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            instance = args[1]

            def findReturnValues(rvalues):
                for value in rvalues.keys():
                    if isinstance(rvalues[value], dict):
                        findReturnValues(rvalues[value])
                    elif isinstance(rvalues[value], unicode):
                        v = yaml.load(rvalues[value])
                        if not isinstance(v, dict) and value in names.keys():
                            kwargs.update({names[value]: rvalues[value]})
                        elif isinstance(v, dict):
                            findReturnValues(v)
                    elif value in names.keys():
                        kwargs.update({names[value]: rvalues[value]})

            findReturnValues(instance.returnValues)

            func(*args, **kwargs)
        return wrapped_func
    return wrapper


def workflow(name, parameters=None, timeout=10):
    if not parameters:
        parameters = dict()

    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            self = args[0]
            instance = args[1]

            assert instance.runWorkflow(name, parameters)
            if not instance.ready(timeout):
                self.fail(
                    "Instance %s don't ready after run workflow: %s with parameters %s and timeout %s".format(
                        instance.instanceId, name, parameters, timeout
                    )
                )
            func(*args, **kwargs)
        return wrapped_func
    return wrapper


# noinspection PyPep8Naming
def instance(byApplication):
    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            self = args[0]

            def findByApplicatioName(app):
                for instance in self.instances:
                    if instance.applicationName == app:
                        return instance
                return None

            func(*args + (findByApplicatioName(byApplication),), **kwargs)
        return wrapped_func
    return wrapper


class BaseTestCase(unittest.TestCase):
    platform = None
    parameters = None
    sandbox = None

    @classmethod
    def environment(cls, organization):
        return {
            "organization": {"name": organization},
            "services": [
                {"type": 'builtin:cobalt_secure_store', "name": 'Keystore', "parameters": "{}"},
                {"type": 'builtin:workflow_service', "name": 'Workflow', "parameters": {'configuration.policies': '{}'}}
            ],
            "instances": [],
            "cloudAccounts": [{
                                  "name": cls.parameters['provider_name'],
                                  "provider": cls.parameters['provider_type'],
                                  "usedEnvironments": [],
                                  "ec2SecurityGroup": "default",
                                  "providerCopy": cls.parameters['provider_type'],
                                  "jcloudsIdentity": cls.parameters['provider_identity'],
                                  "jcloudsCredential": cls.parameters['provider_credential'],
                                  "jcloudsRegions": cls.parameters['provider_region']
            }],
            "environments": [{"name": "default"}]}

    @classmethod
    def apps(cls):
        return []

    @classmethod
    def timeout(cls):
        return 15

    @classmethod
    def setUpClass(cls):
        super(BaseTestCase, cls).setUpClass()
        if cls.parameters['organization']:
            cls.prepare(cls.parameters['organization'], cls.timeout())
        else:
            cls.prepare(cls.__name__, cls.timeout())

    @classmethod
    def prepare(cls, organization, timeout=15):
        cls.sandbox = SandBox(cls.platform, cls.environment(organization))
        cls.organization = cls.sandbox.make()

        cls.instances = []
        for app in cls.sandbox['applications']:
            if app.get('launch', True):
                instance = cls.organization.application(name=app['name']).launch()
                cls.instances.append(instance)
                cls.sandbox.sandbox["instances"].append({"id": instance.instanceId, "name": instance.name})

        for instance in cls.instances:
            if not instance.ready(timeout=timeout):
                cls.sandbox.clean()
                assert False, "Instance %s don't ready".format(instance.instanceId)

    @classmethod
    def tearDownClass(cls):
        super(BaseTestCase, cls).tearDownClass()
        cls.clean()

    @classmethod
    def clean(cls):
        if cls.sandbox:
            cls.sandbox.clean()

    # noinspection PyPep8Naming
    def findByApplicationName(self, name):
        for instance in self.instances:
            if instance.applicationName == name:
                return instance


class SandBox(object):
    def __init__(self, platform, sandbox):
        self.sandbox = sandbox
        self.platform = platform
        self.organization = self.platform.organization(name=self.sandbox["organization"]["name"])

    @staticmethod
    def load_yaml(platform, yaml_file):
        return SandBox(platform, yaml.safe_load(yaml_file))

    def __service(self, environment, service_data):
        service = self.organization.service(type=service_data["type"], name=service_data["name"],
                                            parameters=(service_data["parameters"] or "{}"))
        environment.serviceAdd(service)
        if 'builtin:cobalt_secure_store' in service_data["type"]:
            key_id = service.regenerate()['id']
            environment.policyAdd({
                "action": "provisionVms",
                "parameter": "publicKeyId",
                "value": key_id
            })
        service_data["id"] = service.serviceId

    def __cloud_account(self, environment, provider):
        cloud = self.organization.provider(parameters=provider, name=provider["name"])
        environment.providerAdd(cloud)
        provider["id"] = cloud.providerId

    def __application(self, app):
        manifest = Manifest(url=app["url"])
        application = self.organization.application(manifest=manifest, name=app["name"])
        app["id"] = application.applicationId

    def make(self):
        log.info("preparing sandbox...")

        for env in self.sandbox["environments"]:
            environment = self.organization.environment(name=env["name"])
            environment.clean()

            for service in self.sandbox["services"]:
                self.__service(environment, service)

            for provider in self.sandbox["cloudAccounts"]:
                self.__cloud_account(environment, provider)

            for app in self.sandbox["applications"]:
                self.__application(app)

        log.info("sandbox prepared")

        return self.organization

    def clean(self, timeout=3):
        log.info("cleaning sandbox...")
        for instanceData in self.sandbox['instances']:
            instance = Instance(context=self.platform.context, id=instanceData["id"])
            instance.destroy()
            if not instance.destroyed(timeout):
                log.error(
                    "Instance was not destroyed properly {0}: {1}".format(instanceData["id"], instanceData["name"])
                )
        log.info("sandbox cleaned")

    def __getitem__(self, name):
        if name in self.sandbox:
            return self.sandbox[name]
        else:
            return None