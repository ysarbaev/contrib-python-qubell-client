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
__email__ = "vkhomenko@qubell.com"

import logging as log
import requests
import simplejson as json
from qubell.api.tools import lazy

from qubell.api.tools import waitForStatus as waitForStatus
from qubell.api.private import exceptions
from qubell.api.private.common import EntityList

DEAD_STATUS = ['Destroyed', 'Destroying']


class Instances(EntityList):
    def __init__(self, organization):
        self.organization = organization
        self.auth = self.organization.auth
        self.organizationId = self.organization.organizationId
        EntityList.__init__(self)

    def _generate_object_list(self):
        from qubell.api.private.instance import Instance

        for app in self.organization.applications:
            instances = app.json()['instances']
            instances_alive = [ins for ins in instances if ins['status'] not in ['Destroyed', 'Destroying']]

            for ins in instances_alive:
                self.object_list.append(Instance(self.auth, app, id=ins['id']))


class Instance(object):
    """
    Base class for application instance. Manifest required.
    """

    def __parse(self, values):
        ret = {}
        for val in values:
            ret[val['id']] = val['value']
        return ret

    #@lazy
    def __update(self):
        info = self.json()
        self.name = info['name']
        #self.id = self.instanceId

        self.environmentId = info['environmentId']
        self.environment = self.organization.get_environment(self.environmentId)

    def __init__(self, auth, application, **kwargs):
        if hasattr(self, 'instanceId'):
            log.warning("Instance reinitialized. Dangerous!")
        self.auth = auth
        self.application = application
        self.applicationId = application.applicationId
        self.organization = application.organization
        self.organizationId = application.organizationId
        self.defaultEnvironment = application.defaultEnvironment
        self.__dict__.update(kwargs)
        if 'id' in kwargs:
            self.instanceId = kwargs.get('id')
            self.__update()
        #elif 'name' in kwargs:
        #    self.by_name(kwargs.get('name'))

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
        url = self.auth.api+'/organizations/'+self.organizationId+'/instances/'+self.instanceId+'.json'
        resp = requests.get(url, cookies=self.auth.cookies, data="{}", verify=False)
        log.debug(resp.request.headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.NotFoundError('Unable to get instance properties, got error: %s' % resp.text)

    def create(self, revision=None, environment=None, name=None, parameters={}):
        # Check we already has instance assosiated with us
        if hasattr(self, 'instanceId'):
            return self
        url = self.auth.api+'/organizations/'+self.organizationId+'/applications/'+self.applicationId+'/launch.json'
        headers = {'Content-Type': 'application/json'}
        if environment:
            parameters['environmentId'] = environment.environmentId
        elif not 'environmentId' in parameters.keys():
            parameters['environmentId'] = self.defaultEnvironment.environmentId
        if name:
            parameters['instanceName'] = name

        data = json.dumps(parameters)
        resp = requests.post(url, cookies=self.auth.cookies, data=data, verify=False, headers=headers)

        log.debug('--- INSTANCE LAUNCH REQUEST ---')
        log.debug('REQUEST HEADERS: %s' % resp.request.headers)
        log.debug('REQUEST: %s' % resp.request.body)
        log.debug('RESPONSE: %s' % resp.text)

        if resp.status_code == 200:
            self.instanceId = resp.json()['id']
            self.__update()
            return self
        raise exceptions.ApiError('Unable to launch application id: %s, got error: %s' % (self.applicationId, resp.text))

    def by_name(self, name):
        instance = self.organization.get_instance(name=name)
        #instance = [x for x in self.organization.instances if x.name == name]
        return instance

    def by_id(self, id):
        return self.organization.get_instance(id=id, application=self.application)

    def ready(self, timeout=3):  # Shortcut for convinience. Temeout = 3 min (ask timeout*6 times every 10 sec)
        return waitForStatus(instance=self, final='Running', accepted=['Launching', 'Requested', 'Executing', 'Unknown'], timeout=[timeout*6, 10, 1])
        # TODO: Unknown status  should be removed

        #TODO: not available
    def destroyed(self, timeout=3):  # Shortcut for convinience. Temeout = 3 min (ask timeout*6 times every 10 sec)
        return waitForStatus(instance=self, final='Destroyed', accepted=['Destroying', 'Running'], timeout=[timeout*6, 10, 1])

    def run_workflow(self, name, parameters={}):
        log.info("Running workflow %s" % name)

        url = self.auth.api+'/organizations/'+self.application.organizationId+'/instances/'+self.instanceId+'/workflows/'+name+'.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps(parameters)
        resp = requests.post(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return True
        raise exceptions.ApiError('Unable to run workflow %s, got error: %s' % (name, resp.text))


    def get_manifest(self):
        url = self.auth.api+'/organizations/'+self.application.organizationId+'/applications/'+self.auth.applicationId+'/refreshManifest.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({})
        resp = requests.post(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get manifest, got error: %s' % resp.text)

    def reconfigure(self, name='reconfigured', revision=None, environment=None,  parameters={}):
        revisionId = revision or ''
        submodules = parameters.get('submodules', {})
        url = self.auth.api+'/organizations/'+self.application.organizationId+'/instances/'+self.instanceId+'/configuration.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
                   'parameters': parameters,
                   'submodules': submodules,
                   'revisionId': revisionId,
                   'instanceName': name})
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)

        log.debug('--- INSTANCE RECONFIGUREATION REQUEST ---')
        log.debug('REQUEST HEADERS: %s' % resp.request.headers)
        log.debug('REQUEST: %s' % resp.request.body)
        log.debug('RESPONSE: %s' % resp.text)
        if resp.status_code == 200:
            self.__update()
            return resp.json()
        raise exceptions.ApiError('Unable to reconfigure instance, got error: %s' % resp.text)

    def delete(self):
        return self.destroy()

    def destroy(self):
        log.info("Destroying")
        url = self.auth.api+'/organizations/'+self.application.organizationId+'/instances/'+self.instanceId+'/workflows/destroy.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, cookies=self.auth.cookies, data=json.dumps({}), verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to destroy instance, got error: %s' % resp.text)

    def __del__(self):
        pass
