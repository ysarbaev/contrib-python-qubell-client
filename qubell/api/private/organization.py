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
__version__ = "1.0.5"
__email__ = "vkhomenko@qubell.com"

import logging as log

import requests
import simplejson as json

from qubell.api.private.platform import QubellPlatform
from qubell.api.private import exceptions


class Organization(QubellPlatform):

    def __init__(self, context, id):
        self.context = context
        self.organizationId = id

        my = self.json()
        self.name = my['name']
        backends = my['backends']
        zones = [bk for bk in backends if bk['isDefault']==True]
        if len(zones):
            self.zoneId = zones[0]['id']
        else:
            self.zoneId = self.list_zones()[0]['id'] # TODO: Think about how to choose zone
        self.context.zoneId = self.zoneId

    def __getattr__(self, key):
        resp = self.json()
        if not resp.has_key(key):
            raise exceptions.NotFoundError('Cannot get property %s' % key)
        return resp[key] or False

    def json(self):
        url = self.context.api+'/organizations.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            org = [x for x in resp.json() if x['id'] == self.organizationId]
            if len(org)>0:
                return org[0]
            return resp.json()
        raise exceptions.ApiError('Unable to get organization by id %s, got error: %s' % (self.organizationId, resp.text))

### APPLICATION
    def create_application(self, name, manifest):
        log.info("Creating application: %s" % name)
        url = self.context.api+'/organizations/'+self.organizationId+'/applications.json'

        resp = requests.post(url, files={'path': manifest.content}, data={'manifestSource': 'upload', 'name': name}, verify=False, cookies=self.context.cookies)
        log.debug(resp.text)
        if resp.status_code == 200:
            return self.get_application(resp.json()['id'])
        raise exceptions.ApiError('Unable to create application %s, got error: %s' % (name, resp.text))

    def get_application(self, id):
        log.info("Picking application: %s" % id)
        self.context.organizationId = self.organizationId
        from qubell.api.private.application import Application
        return Application(self.context, id=id)

    def list_applications(self):
        url = self.context.api+'/organizations/'+self.organizationId+'/applications.json'
        resp = requests.get(url, cookies=self.context.cookies, data="{}", verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get applications list, got error: %s' % resp.text)

    def delete_application(self, id):
        app = self.get_application(id)
        return app.delete()

    def application(self, id=None, manifest=None, name=None):
        """ Smart object. Will create application or pick one, if exists"""
        if name:
            appz = [app for app in self.list_applications() if app['name'] == name]
            # app found by name
            if len(appz):
                return self.get_application(appz[0]['id']) # pick first
            else:
                return self.create_application(name, manifest)
        else:
            name = 'generated-app-name'
            if id:
                return self.get_application(id)
            else:
                return self.create_application(name, manifest)

### SERVICE
    def create_service(self, name, type, parameters={}, zone=None):
        log.info("Creating service: %s" % name)
        if not zone:
            zone = self.zoneId
        data = {'name': name,
                'typeId': type,
                'zoneId': zone,
                'parameters': parameters}

        url = self.context.api+'/organizations/'+self.organizationId+'/services.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, cookies=self.context.cookies, data=json.dumps(data), verify=False, headers=headers)
        log.debug(resp.request.body)
        log.debug(resp.text)

        if resp.status_code == 200:
            return self.get_service(resp.json()['id'])
        raise exceptions.ApiError('Unable to create service %s, got error: %s' % (name, resp.text))

    def create_keystore_service(self, name='generated-keystore', parameters={}, zone=None):
        return self.create_service(name=name, type='builtin:cobalt_secure_store', parameters=parameters, zone=zone)

    def create_workflow_service(self, name='generated-workflow', policies={}, zone=None):
        parameters = {'configuration.policies': json.dumps(policies)}
        return self.create_service(name=name, type='builtin:workflow_service', parameters=parameters, zone=zone)

    def create_shared_service(self, name='generated-shared', instances={}, zone=None):
        parameters = {'configuration.shared-instances': json.dumps(instances)}
        return self.create_service(name=name, type='builtin:shared_instances_catalog', parameters=parameters, zone=zone)

    def get_service(self, id):
        log.info("Picking service: %s" % id)
        self.context.organizationId = self.organizationId
        from qubell.api.private.service import Service
        return Service(self.context, id=id)

    def list_services(self):
        url = self.context.api+'/organizations/'+self.organizationId+'/services.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.request.body)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get services list, got error: %s' % resp.text)

    def delete_service(self, id):
        srv = self.get_service(id)
        return srv.delete()

    def service(self, id=None, name=None, type=None, parameters={}, zone=None):
        """ Smart object. Will create service or pick one, if exists"""
        if name:
            servs = [srv for srv in self.list_services() if srv['name'] == name]
            # service found by name
            if len(servs):
                return self.get_service(servs[0]['id']) # pick first
            elif type:
                return self.create_service(name, type, parameters, zone)
        else:
            name = 'generated-service'
            if id:
                return self.get_service(id)
            elif type:
                return self.create_service(name, type, parameters, zone)
        raise exceptions.NotFoundError('Service not found or not enough parameters to create service: %s' % name)

### ENVIRONMENT
    def create_environment(self, name, default=False, zone=None):
        log.info("Creating environment: %s" % name)
        if not zone:
            zone = self.context.zoneId
        data = {'isDefault': default,
                'name': name,
                'backend': zone,
                'organizationId': self.organizationId}

        url = self.context.api+'/organizations/'+self.organizationId+'/environments.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, cookies=self.context.cookies, data=json.dumps(data), verify=False, headers=headers)
        log.debug(resp.request.body)
        log.debug(resp.text)

        if resp.status_code == 200:
            return self.get_environment(resp.json()['id'])
        raise exceptions.ApiError('Unable to create environment %s, got error: %s' % (name, resp.text))

    def list_environments(self):
        url = self.context.api+'/organizations/'+self.organizationId+'/environments.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get environments list, got error: %s' % resp.text)

    def get_environment(self, id):
        from qubell.api.private.environment import Environment
        self.context.organizationId = self.organizationId
        self.context.environmentId = id
        return Environment(self.context, id)

    def delete_environment(self, id):
        env = self.get_environment(id)
        return env.delete()

    def environment(self, id=None, name=None, zone=None, default=False):
        """ Smart object. Will create environment or pick one, if exists"""
        if name:
            envs = [env for env in self.list_environments() if env['name'] == name]
            # environment found by name
            if len(envs):
                return self.get_environment(envs[0]['id']) # pick first
            else:
                return self.create_environment(name=name, zone=zone, default=default)
        else:
            name = 'generated-env'
            if id:
                return self.get_environment(id)
            else:
                return self.create_environment(name=name, zone=zone, default=default)

    def set_default_environment(self, id):
        url = self.context.api+'/organizations/'+self.organizationId+'/defaultEnvironment.json'
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'environmentId': id})
        resp = requests.put(url, cookies=self.context.cookies, data=data, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to set default environment, got error: %s' % resp.text)

### PROVIDER
    def create_provider(self, name, parameters):
        log.info("Creating provider: %s" % name)
        parameters['name'] = name

        url = self.context.api+'/organizations/'+self.organizationId+'/providers.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, cookies=self.context.cookies, data=json.dumps(parameters), verify=False, headers=headers)
        log.debug(resp.text)

        if resp.status_code == 200:
            return self.get_provider(resp.json()['id'])
        raise exceptions.ApiError('Unable to create environment %s, got error: %s' % (name, resp.text))

    def list_providers(self):
        url = self.context.api+'/organizations/'+self.organizationId+'/providers.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get providers list, got error: %s' % resp.text)

    def get_provider(self, id):
        from qubell.api.private.provider import Provider
        self.context.organizationId = self.organizationId
        return Provider(context=self.context, id=id)

    def delete_provider(self, id):
        prov = self.get_provider(id)
        return prov.delete()

    def provider(self, id=None, name=None, parameters=None):
        """ Smart object. Will create provider or pick one, if exists"""
        if name:
            provs = [prov for prov in self.list_providers() if prov['name'] == name]
            # provider found by name
            if len(provs):
                return self.get_provider(provs[0]['id']) # pick first
            elif parameters:
                return self.create_provider(name=name, parameters=parameters)
        else:
            name = 'generated-provider'
            if id:
                return self.get_provider(id)
            elif parameters:
                return self.create_provider(name=name, parameters=parameters)
        raise exceptions.NotFoundError('Provider not found or not enough parameters to create provider: %s' % name)

### ZONES

    def list_zones(self):
        url = self.context.api+'/organizations/'+self.organizationId+'/zones.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get zones list, got error: %s' % resp.text)