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

from qubell.api.private import exceptions
from qubell.api.private.common import QubellEntityList

DEAD_STATUS = ['Destroyed', 'Destroying']


class Environments(QubellEntityList):
    def __init__(self, organization):
        # TODO: That should be done by parent
        QubellEntityList.__init__(self, organization)

    def _generate_object_list(self):
        for env in self.organization.list_environments_json():
            self.object_list.append(Environment(self.auth, self.organization, id=env['id']))

class Environment(object):
    def __update(self):
        info = self.json()
        self.name = info['name']
        self.id = self.environmentId
        self.zoneId = info['backends'][0]['id']
        self.isDefault = info['isDefault']

    def __init__(self, auth, organization, **kwargs):
        if 'environmentId' in locals():
            log.warning("Environment reinitialized. Dangerous!")
        self.services = []
        self.policies = []
        self.markers = []
        self.properties = []
        self.providers = []
        self.auth = auth
        self.organization = organization
        self.organizationId = self.organization.organizationId
        if 'id' in kwargs:
            self.environmentId = kwargs.get('id')
            self.__update()

    def __getattr__(self, key):
        resp = self.json()
        if not resp.has_key(key):
            raise exceptions.NotFoundError('Cannot get property %s' % key)
        return resp[key] or False

    def create(self, name, zone=None, default=False):
        log.info("Creating environment: %s" % name)
        if not zone:
            zone = self.organization.zone.zoneId
        data = {'isDefault': default,
                'name': name,
                'backend': zone,
                'organizationId': self.organizationId}

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, cookies=self.auth.cookies, data=json.dumps(data), verify=False, headers=headers)
        log.debug(resp.request.body)
        log.debug(resp.text)

        if resp.status_code == 200:
            self.environmentId = resp.json()['id']
            self.__update()
            return self
        raise exceptions.ApiError('Unable to create environment %s, got error: %s' % (name, resp.text))

    def restore(self, config):
        for marker in config.pop('markers', []):
            self.add_marker(marker)
        for policy in config.pop('policies', []):
            self.add_policy(policy)
        for property in config.pop('properties', []):
            self.add_property(**property)
        for provider in config.pop('providers', []):
            prov = self.organization.get_or_create_provider(id=provider.pop('id', None), name=provider.pop('name'), parameters=provider)
            self.add_provider(prov)
        for service in config.pop('services', []):
            serv = self.organization.get_or_create_service(id=service.pop('id', None), name=service.pop('name'), type=service.pop('type', None))
            self.add_service(serv)
            if serv.type == 'builtin:cobalt_secure_store':
                # TODO: We do not need to regenerate key every time. Find better way.
                myenv = self.organization.get_environment(self.environmentId)
                myenv.add_policy(
                    {"action": "provisionVms",
                     "parameter": "publicKeyId",
                     "value": serv.regenerate()['id']})

    def json(self):
        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        resp = requests.get(url, cookies=self.auth.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get environment properties, got error: %s' % resp.text)

    def delete(self):
        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.delete(url, cookies=self.auth.cookies, data=json.dumps({}), verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return True
        raise exceptions.ApiError('Unable to delete environment %s, got error: %s' % (self.environmentId, resp.text))

    def set_as_default(self):
        url = self.auth.api+'/organizations/'+self.organizationId+'/defaultEnvironment.json'
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'environmentId': self.id})
        resp = requests.put(url, cookies=self.auth.cookies, headers=headers, data=data, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to set default environment, got error: %s' % resp.text)


    def list_available_services(self):
        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'/availableServices.json'
        resp = requests.get(url, cookies=self.auth.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)


    def add_service(self, service):
        data = self.json()
        data['serviceIds'].append(service.serviceId)
        data['services'].append(service.json())

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            self.services.append(service)
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)


    def remove_service(self, service):
        data = self.json()
        data['serviceIds'].remove(service.serviceId)
        data['services'].remove(service.json())

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            self.services.remove(service)
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)

    def add_marker(self, marker):
        data = self.json()
        data['markers'].append({'name': marker})

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            self.markers.append(marker)
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)


    def remove_marker(self, marker):
        data = self.json()
        data['markers'].remove({'name': marker})

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            self.markers.remove(marker)
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)


    def add_property(self, name, type, value):
        data = self.json()
        data['properties'].append({'name': name, 'type': type, 'value': value})

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            self.properties.append({'name': name, 'type': type, 'value': value})
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)


    def remove_property(self, name):
        data = self.json()
        property = [p for p in data['properties'] if p['name'] == name]
        if len(property)<1:
            log.error('Unable to remove property %s. Not found.' % name)
        data['properties'].remove(property[0])

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            # TODO: make removal
            #self.properties.pop(name)
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)



    def clean(self):
        data = self.json()
        data['serviceIds'] = []
        data['services'] = []

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)


    def add_policy(self, new):
        data = self.json()
        data['policies'].append(new)

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            self.policies.append(new)
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)

    def remove_policy(self):
        raise NotImplementedError

    def add_provider(self, provider):
        data = self.json()
        data.update({'providerId': provider.providerId})

        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            self.providers.append(provider)
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)

    def remove_provider(self):
        raise NotImplementedError

    def set_backend(self, zone):
        data = self.json()
        data.update({'backend': zone.zoneId})
        url = self.auth.api+'/organizations/'+self.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.auth.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to update environment, got error: %s' % resp.text)