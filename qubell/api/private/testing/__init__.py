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

__email__ = "apanasenko@qubell.com"

import unittest
import yaml
import logging as log
import re
import sys

from functools import wraps

from qubell.api.globals import *
from qubell.api.private.service import COBALT_SECURE_STORE_TYPE, WORKFLOW_SERVICE_TYPE, CLOUD_ACCOUNT_TYPE
from qubell.api.private.exceptions import NotFoundError

import logging

import requests
from nose.plugins.skip import SkipTest

logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.ERROR)


def norm(name):
    return str(re.sub("[^a-zA-Z0-9_]+", "_", name))

def format_as_api(data):
    """
    Accepts {'default':{},}
    returns [{'name':'default',}]
    """
    result = []
    if isinstance(data, dict):
        for name, value in data.items():
            key = norm(name)
            value.update({'name': name})
            result.append(value)
        return result
    else:
        return data

def values(names):
    """
    Method decorator that allows inject return values into method parameters.
    It tries to find desired value going deep. For convinience injects list with only one value as value.
    :param names: dict of "value-name": "method-parameter-name"
    """
    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
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

def _parameterize(case, params):
        '''This generates the classes (in the sense that it's a generator.)
        '''
        # based on: https://code.google.com/p/parameterized-testcase/
        case_mod = sys.modules[case.__module__]
        for env_name, param_set in params.items():
            if env_name=='default':
                new_cls=case
            else:
                attrs = dict(case.__dict__)
                attrs.update({'className': env_name})
                new_cls = type('{0}_{1}'.format(case.__name__, env_name), (case,), attrs)
                setattr(case_mod, new_cls.__name__, new_cls)
            new_cls.current_environment=env_name
            yield new_cls

def parameterize(case, params):
    return list(_parameterize(case=case, params=params))

def environment(params):
    def wraps_class(clazz):
        parameterize(clazz, params)
        return clazz
    return wraps_class
environments = environment

def applications(appsdata):
    """
    Class decorator that allows to crete applications and start instances there.
    If used with environment decorator, instances would be started for every env.
    :param appdata: list
    """
    # TODO: Combine with parameterize
    def wraps_class(clazz):
        if "applications" in clazz.__dict__:
            log.warn("Class {0} applications attribute is overridden".format(clazz.__name__))
        for appdata in appsdata:
            appdata['name'] = norm(appdata['name'])
            if appdata.get('add_as_service'):
                start_name='test00_launch_%s' % appdata['name']
                destroy_name='testzz_destroy_%s' % appdata['name']
            else:
                start_name='test01_launch_%s' % appdata['name']
                destroy_name='testzy_destroy_%s' % appdata['name']

            clazz.applications.append(appdata)
            if appdata.get('launch', True):
                parameters = appdata.get('parameters', {})
                settings = appdata.get('settings', {})
                _add_launch_test(clazz, test_name=start_name, app_name=appdata['name'], parameters=parameters, settings=settings)
                _add_destroy_test(clazz, test_name=destroy_name, app_name=appdata['name'])
                log.info("Test '{0}' added as instance launch test for {1}".format(start_name, clazz.__name__))
        return clazz
    return wraps_class
application = applications

def _add_launch_test(cls, test_name, app_name, parameters, settings):
    def test_method(self):
        self._launch_instance(app_name, parameters, settings)
    setattr(cls, test_name, test_method)
    test_method.__name__ = test_name
    #test_method.__doc__ = "Autogenerated %s" % test_name

def _add_destroy_test(cls, test_name, app_name):
    def test_method(self):
        self._destroy_instance(app_name)
    setattr(cls, test_name, test_method)
    test_method.__name__ = test_name
    #test_method.__doc__ = "Autogenerated %s" % test_name

# noinspection PyPep8Naming
def instance(byApplication):
    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            self = args[0]

            ins = self.find_by_application_name(norm(byApplication))
            if not ins.running():
                raise SkipTest("Instance %s not in Running state" % ins.name)
            func(*args + (ins,), **kwargs)
        return wrapped_func
    return wrapper


class BaseTestCase(unittest.TestCase):
    platform = None
    parameters = None
    sandbox = None
    environments = None
    applications = []
    service_instances = []
    regular_instances = []
    instances = []
    current_environment = 'default'

    @classmethod
    def environment(cls, organization):
        provider_config = {'configuration.provider': cls.parameters['provider_type'],
                           'configuration.legacy-regions': cls.parameters['provider_region'],
                           'configuration.endpoint-url': '',
                           'configuration.legacy-security-group': '',
                           'configuration.identity': cls.parameters['provider_identity'],
                           'configuration.credential': cls.parameters['provider_credential']}

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

    @classmethod
    def setUpClass(cls):
        super(BaseTestCase, cls).setUpClass()
        if cls.parameters['organization']:
            cls.prepare(cls.parameters['organization'], cls.timeout())
        else:
            cls.prepare(cls.__name__, cls.timeout())

    @classmethod
    def tearDownClass(cls):
        super(BaseTestCase, cls).tearDownClass()

    def _launch_instance(self, app_name, parameters, settings, timeout=30):
        application = self.organization.applications[app_name]
        environment = self.organization.environments[self.current_environment]
        instance = self.organization.create_instance(application=application,
                                                    environment=environment,
                                                    parameters=parameters,
                                                    **settings)
        self.assertTrue(instance.ready(timeout=timeout), "App {0} failed to start instance in env {1}. Status: {2}. Timeout: {3}".format(app_name, self.current_environment, instance.status, timeout))

        # Hack to recognize service
        if 'test00_launch_' in self._testMethodName:
            environment.add_service(instance)
            self.service_instances.append(instance)
        else:
            self.regular_instances.append(instance)
        self.instances = self.service_instances+self.regular_instances

    def _destroy_instance(self, app_name, timeout=30):
        instance = self.find_by_application_name(app_name)

        if os.getenv("QUBELL_DEBUG", None) and not('false' in os.getenv("QUBELL_DEBUG", None)):
            log.info("QUBELL_DEBUG is ON\n DO NOT clean sandbox")
        else:
            instance.destroy()
            assert instance.destroyed(timeout=timeout)
        if 'testzz_destroy_' in self._testMethodName:
            self.service_instances.remove(instance)
        else:
            self.regular_instances.remove(instance)
        self.instances = self.service_instances+self.regular_instances

    @classmethod
    def prepare(cls, organization, timeout=30):
        """ Create sandboxed test environment
        """
        log.info("\n\n\n---------------  Preparing sandbox...  ---------------")
        cls.sandbox = SandBox(cls.platform, cls.environment(organization))
        cls.organization = cls.sandbox.make()

        # If 'meta' in sandbox, restore applications that comes in meta before.
        # TODO: all this stuff needs refactoring.
        apps = []
        if cls.__dict__.get('meta'):
            meta_raw = requests.get(url=cls.__dict__.get('meta'))
            meta = yaml.safe_load(meta_raw.content)
            for app in meta['kit']['applications']:
                apps.append({
                    'name': app['name'],
                    'url': app['manifest']})
            cls.organization.restore({'applications':apps})
        log.info("---------------  Sandbox prepeared  ---------------\n\n\n")

    def find_by_application_name(self, name):
        for inst in self.regular_instances+self.service_instances:
            if inst.application.name == name and inst.environment.name == self.current_environment:
                return inst
        raise NotFoundError

class SandBox(object):
    def __init__(self, platform, sandbox):
        self.sandbox = sandbox
        self.platform = platform
        self.organization = self.platform.organization(name=self.sandbox["organization"]["name"])
        self.sandbox['instances'] = sandbox.get('instances', [])


    @staticmethod
    def load_yaml(platform, yaml_file):
        return SandBox(platform, yaml.safe_load(yaml_file))

    def make(self):
        self.organization.restore(self.sandbox)
        return self.organization

    def clean(self):
        # TODO: need cleaning mechanism
        pass

    def __check_environment_name(self, name):
        import re
        re.sub("")

    def __getitem__(self, name):
        if name in self.sandbox:
            return self.sandbox[name]
        else:
            return None
