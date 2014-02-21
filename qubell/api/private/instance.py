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
import warnings
from qubell import deprecated
from qubell.api.private.environment import EnvironmentList

__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__email__ = "vkhomenko@qubell.com"

import logging as log
import simplejson as json
from qubell.api.tools import lazyproperty

from qubell.api.tools import waitForStatus as waitForStatus
from qubell.api.private import exceptions
from qubell.api.private.common import QubellEntityList
from qubell.api.provider.router import ROUTER as router

DEAD_STATUS = ['Destroyed', 'Destroying']

class Instance(object):
    """
    Base class for application instance. Manifest required.
    """

    def __parse(self, values):
        ret = {}
        for val in values:
            ret[val['id']] = val['value']
        return ret

    def __init__(self, organization, id=None, auth=None, **kwargs):
        if hasattr(self, 'instanceId'):
            log.warning("Instance reinitialized. Dangerous!")
        if auth:
            warnings.warn("'auth' param is deprecated, and will be removed soon", DeprecationWarning, stacklevel=2)
            self.auth = auth
        self.organization = organization
        self.organizationId = organization.organizationId
        self.__dict__.update(kwargs)
        if id:
            self.instanceId = id
            self.json()

    @lazyproperty
    def applicationId(self): return self.json()["applicationId"]

    @lazyproperty
    def application(self):
        return self.organization.applications[self.applicationId]

    @lazyproperty
    def environmentId(self): return self.json()['environmentId']

    @lazyproperty
    def environment(self): return self.organization.get_environment(self.environmentId)

    @property
    def status(self): return self.json()["status"]

    @property
    def name(self): return self.json()["name"]

    def __getattr__(self, key):
        if key in ['instanceId',]:
            raise exceptions.NotFoundError('Unable to get instance property: %s' % key)
        if key == 'ready':
            log.debug('Checking instance status')
            return self.ready()
        # return same way old_public api does
        if key in ['returnValues', ]:
            return self.__parse(self.json()[key])
        else:
            log.debug('Getting instance attribute: %s' % key)
            return self.json()[key]

    def json(self):
        return router.get_instance(org_id=self.organizationId, instance_id=self.instanceId).json()

    @staticmethod
    def new(application=None, revision=None, environment=None, name=None, parameters={}):
        if environment:
            parameters['environmentId'] = environment.environmentId
        elif not 'environmentId' in parameters.keys():
            parameters['environmentId'] = application.organization.defaultEnvironment.environmentId
        if name:
            parameters['instanceName'] = name

        data = json.dumps(parameters)
        resp = router.post_organization_instance(org_id=application.organizationId, app_id=application.applicationId, data=data)
        return Instance(organization=application.organization, id=resp.json()['id'])

    @deprecated("Use static method 'Instance.new' instead")
    def create(self, application=None, revision=None, environment=None, name=None, parameters={}):
        # Check we already has instance associated with us
        if hasattr(self, 'instanceId'):
            return self

        assert application, "Api changed, define 'application' explicitly to create"
        return Instance.new(application, revision, environment, name, parameters)

    def by_name(self, name):
        instance = self.organization.get_instance(name=name)
        #instance = [x for x in self.organization.instances if x.name == name]
        return instance

    def by_id(self, id):
        return Instance(id=id, organization=self.organization)

    def ready(self, timeout=3):  # Shortcut for convinience. Temeout = 3 min (ask timeout*6 times every 10 sec)
        return waitForStatus(instance=self, final='Running', accepted=['Launching', 'Requested', 'Executing', 'Unknown'], timeout=[timeout*6, 10, 1])
        # TODO: Unknown status  should be removed

        #TODO: not available
    def destroyed(self, timeout=3):  # Shortcut for convinience. Temeout = 3 min (ask timeout*6 times every 10 sec)
        return waitForStatus(instance=self, final='Destroyed', accepted=['Destroying', 'Running'], timeout=[timeout*6, 10, 1])

    def run_workflow(self, name, parameters={}):
        log.info("Running workflow %s" % name)
        router.post_instance_workflow(org_id=self.organizationId, instance_id=self.instanceId, wf_name=name, data=json.dumps(parameters))
        return True

    def get_manifest(self):
        return router.post_application_refresh(org_id=self.organizationId, app_id=self.applicationId).json()

    def reconfigure(self, name='reconfigured', revision=None, environment=None,  parameters={}):
        revisionId = revision or ''
        submodules = parameters.get('submodules', {})

        payload = json.dumps({
                   'parameters': parameters,
                   'submodules': submodules,
                   'revisionId': revisionId,
                   'instanceName': name})
        resp = router.put_instance_configuration(org_id=self.organizationId, instance_id=self.instanceId, data=payload)
        return resp.json()

    def delete(self):
        return self.destroy()

    def destroy(self):
        log.info("Destroying")
        resp = router.post_instance_workflow(org_id=self.organizationId, instance_id=self.instanceId, wf_name="destroy")
        return resp.json()

    @property
    def serve_environments(self):
        return EnvironmentList(lambda: self.json()["environments"], organization=self.organization)

    def add_as_service(self, environments=None, environment_ids=None):
        assert environments or environment_ids
        if environments:
            data = [env.environmentId for env in environments]
        else:
            assert isinstance(environment_ids, list)
            data = environment_ids
        router.post_instance_services(org_id=self.organizationId, instance_id=self.instanceId, data=json.dumps(data))

class InstanceList(QubellEntityList):
    base_clz = Instance