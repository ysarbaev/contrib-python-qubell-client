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
from qubell.api.public import application

__author__ = "Anton Panasenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"

__email__ = "apanasenko@qubell.com"

import unittest
import yaml
import logging as log

from functools import wraps

from qubell.api.private.instance import Instance
from qubell.api.private.manifest import Manifest
from qubell.api.private.service import system_application_types, COBALT_SECURE_STORE_TYPE, WORKFLOW_SERVICE_TYPE


from requests import api
from requests import sessions

import time
import logging
import re
import types
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARN)

def values(names):
    """
    Method decorator that allows inject return values into method parameters.
    It tries to find desired value going deep. For convinience injects list with only one value as value.
    :param names: dict of "value-name": "method-parameter-name"
    """
    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            instance = None
            if len(args)>1:
                instance=args[1]
            else:
                instance = kwargs['instance']

            def findReturnValues(rvalues):
                for k, v in rvalues.iteritems():
                    if isinstance(v, dict):
                        findReturnValues(v) #go deep, to find desired name
                    if k in names.keys():
                        if isinstance(v,list) and len(v)==1:
                            kwargs.update({names[k]: v[0]})
                        else:
                            kwargs.update({names[k]: v})

            findReturnValues(instance.returnValues)

            #ensure all names was set
            missing_params = [k for k, v in names.items() if v not in kwargs]
            if missing_params:
                raise AttributeError("Parameters {0} for '{1}' were not found".format(missing_params, func.__name__), missing_params)

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

            assert instance.run_workflow(name, parameters)
            if not instance.ready(timeout):
                self.fail(
                    "Instance %s isn't ready in appropriate time: %s with parameters %s and timeout %s" % (
                        instance.instanceId, name, parameters, timeout
                    )
                )
            func(*args, **kwargs)
        return wrapped_func
    return wrapper


def environment(params):
    """
    Class decorator that allows to run tests in sandbox against different Qubell environments.
    Each test method in suite is converted to <test_name>_on_environemnt_<environment_name>
    :param params: dict
    """
    assert isinstance(params, dict), "@environment decorator should take 'dict' with environments"

    def copy(func, name=None):
        return types.FunctionType(func.func_code, func.func_globals, name=name,
                                  argdefs=func.func_defaults,
                                  closure=func.func_closure)

    def wraps_class(clazz):
        if "environments" in clazz.__dict__:
            log.warn("Class {0} environment attribute is overriden".format(clazz.__name__))

        clazz.environments = params

        methods = [method
                   for _, method in clazz.__dict__.items()
                   if isinstance(method, types.FunctionType) and method.func_name.startswith("test") ]

        for method in methods:
            delattr(clazz, method.func_name)
            log.info("Test '{0}' multiplied per environment in {1}".format(method.func_name, clazz.__name__))
            for env_name in params.keys():
                new_name = method.func_name + "_on_environment_" + env_name
                setattr(clazz, new_name, copy(method, new_name))

        return clazz
    return wraps_class


# noinspection PyPep8Naming
def instance(byApplication):
    def wrapper(func):
        def get_environment_name(self, f):
            separator = "_on_environment_"
            if len(f.__name__.split(separator)) > 1:
                env = f.__name__.split(separator)[1]
            elif "_testMethodName" in self.__dict__ and len(self._testMethodName.split(separator)) > 1:
                env = self._testMethodName.split(separator)[1]
            else:
                env = "default"
            return env

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            self = args[0]
            env = get_environment_name(self, func)

            def find_by_application_name(app):
                for inst in self.instances:
                    if inst.applicationName == app and inst.environmentName == env:
                        return inst
                return None

            func(*args + (find_by_application_name(byApplication),), **kwargs)
        return wrapped_func
    return wrapper


class BaseTestCase(unittest.TestCase):
    platform = None
    parameters = None
    sandbox = None
    environments = None

    @classmethod
    def environment(cls, organization):
        import re
        if cls.environments:
            envs = {}
            servs = []
            for name, value in cls.environments.items():
                key = str(re.sub("[^a-zA-Z0-9_]", "", name))
                envs.update({key: value})

        else:
            envs = {"default": {}}

        servs = [{"type": COBALT_SECURE_STORE_TYPE, "name": 'Default credentials service'},
                 {"type": WORKFLOW_SERVICE_TYPE, "name": 'Default workflow service', "parameters": {'configuration.policies': '{}'}}]

        return {
            "organization": {"name": organization},
            "services": servs,
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
            "environments": envs}

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
    def prepare(cls, organization, timeout=30):
        cls.sandbox = SandBox(cls.platform, cls.environment(organization))
        cls.organization = cls.sandbox.make()
        cls.instances = []

        def launch_in_env(app, env):
            environment = cls.organization.environment(name=env)
            parameters = {'parameters': app.get('parameters', {})}
            instance = cls.organization.applications[app['name']].launch(
                environment=environment, parameters=parameters)
            cls.instances.append(instance)
            if app.get('add_as_service', False):
                environment.add_service(instance)
            cls.sandbox.sandbox["instances"].append({
                "id": instance.instanceId,
                "name": instance.name,
                "applicationId":  app['id']
            })
            return instance

        def check_instances(instances):
            for instance in cls.instances:
                if not instance.ready(timeout=timeout):
                    cls.sandbox.clean()
                    assert False, "Instance %s not ready after timeout" % instance.instanceId

        # launch service instances first
        for app in cls.sandbox['applications']:
            for env in cls.sandbox['environments']:
                if app.get('launch', True) and app.get('add_as_service', False):
                    launch_in_env(app, env)
        check_instances(cls.instances)

        # then launch non-service instances
        regular_instances = []
        for app in cls.sandbox['applications']:
            for env in cls.sandbox['environments']:
                if app.get('launch', True) and not app.get('add_as_service', False):
                    regular_instances.append(launch_in_env(app, env))
        check_instances(regular_instances)

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

        application = self.organization.applications[system_application_types.get(service_data["type"],service_data["type"])]
        service = self.organization.service(application=application, name=service_data["name"],
                                            environment=environment,
                                            parameters=(service_data.get("parameters")))
        service.ready(1)
        environment.add_service(service)
        if COBALT_SECURE_STORE_TYPE is service_data["type"]:
            key_id = service.regenerate()['id']
            environment.add_policy({
                "action": "provisionVms",
                "parameter": "publicKeyId",
                "value": key_id
            })
        service_data["id"] = service.instanceId

    def __cloud_account(self, environment, provider):
        cloud = self.organization.provider(parameters=provider, name=provider["name"])
        environment.add_provider(cloud)
        provider["id"] = cloud.providerId

    def __application(self, app):
        manifest = Manifest(**{k: v for k, v in app.iteritems() if k in ["content", "url", "file"]})
        application = self.organization.application(manifest=manifest, name=app["name"])
        app["id"] = application.applicationId

    def make(self):
        log.info("Preparing sandbox...")

        for app in self.sandbox["applications"]:
            self.__application(app)

        for name, env in self.sandbox["environments"].items():
            environment = self.organization.environment(name=name)
            environment.clean()

            for service in self.sandbox["services"] + env.get('services', []):
                self.__service(environment, service)

            for provider in self.sandbox["cloudAccounts"] + env.get('cloudAccounts', []):
                self.__cloud_account(environment, provider)

            for police in env.get('policies', []):
                environment.add_policy(police)

        log.info("Sandbox prepared")

        return self.organization

    def clean(self, timeout=10):
        log.info("Cleaning sandbox...")

        def destroy(test_instances):
            instances = self.organization.instances
            services_to_destroy = []
            instances_to_destroy = []
            for instanceData in test_instances:
                if instanceData['id'] in instances: #someone may removed it already
                    instance = instances[instanceData['id']]
                    if instance.serve_environments:
                        services_to_destroy.append(instance)
                    else:
                        instances_to_destroy.append(instance)

            # destroy non-service instances first
            for instance in instances_to_destroy:
                instance.destroy()
            for instance in services_to_destroy:
                instance.destroy()

            return services_to_destroy + instances_to_destroy

        for instance in destroy(self.sandbox['instances']):
            if not instance.destroyed(timeout):
                log.error(
                    "Instance was not destroyed properly {0}: {1}", instance.id, instance.name
                )

        log.info("Sandbox cleaned")

    def __check_environment_name(self, name):
        import re
        re.sub("")

    def __getitem__(self, name):
        if name in self.sandbox:
            return self.sandbox[name]
        else:
            return None