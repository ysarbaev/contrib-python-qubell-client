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

import requests
import logging as log
from qubellclient.private.organization import Organization
import simplejson as json

class Environment(Organization):

    def __init__(self, context, id=None, name='default'):
        self.name = name
        self.context = context
        if id:
            self.environmentId = id
        else:
            self.environmentId = self.list()[0]['id'] # TODO
        self.context.environmentId = self.environmentId

    def list(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def json(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def servicesAvailable(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'/availableServices.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def serviceAdd(self, service):
        data = self.json()
        data['serviceIds'].append(service.serviceId)
        data['services'].append(service.json())

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def serviceRemove(self, service):
        data = self.json()
        data['serviceIds'].remove(service.serviceId)
        data['services'].remove(service.json())

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False


    def markerAdd(self, marker):
        data = self.json()
        data['markers'].append({'name': marker})

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def markerRemove(self, marker):
        data = self.json()
        data['markers'].remove({'name': marker})

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False


    def propertyAdd(self, name, type, value):
        data = self.json()
        data['properties'].append({'name': name, 'type': type, 'value': value})

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def propertyRemove(self, name):
        data = self.json()
        property = [p for p in data['properties'] if p['name'] == name]
        if len(property)<1:
            log.error('Unable to remove property %s. Not found.' % name)
        data['properties'].remove(property[0])

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False


    def clean(self):
        data = self.json()
        data['serviceIds'] = []
        data['services'] = []

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def __getattr__(self, item):
        return self.json()[item]

    def policyAdd(self, new):
        data = self.json()
        data['policies'].append(new)

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def providerAdd(self, provider):
        data = self.json()
        data.update({'providerId': provider.providerId})

        url = self.context.api+'/organizations/'+self.context.organizationId+'/environments/'+self.environmentId+'.json'
        payload = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp = requests.put(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False
