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

from qubellclient.private.organization import Organization
import requests
import simplejson as json

import logging as log

class Service(Organization):
    rawResponse = None

    def __init__(self, context, id=None, name=None, type=None, parameters={}):
        self.name = name
        self.type = type
        self.context = context

        # Create service
        if not id:
            self.serviceId = self._create(parameters)['id']
        # Service exists, init.
        else:
            self.serviceId = id

    def _create(self, parameters):
        data = {
            "name": self.name,
            "typeId": self.type,
            "zoneId": self.context.zoneId}

        if 'builtin:shared_instances_catalog' in self.type:
            data['parameters'] = {'configuration.shared-instances': parameters}
        elif 'builtin:workflow_service' in self.type:
            data['parameters'] = {'configuration.policies': parameters}
        else:
            data['parameters'] = parameters


        payload = json.dumps(data)
        url = self.context.api+'/organizations/'+self.context.organizationId+'/services.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)

        self.rawResponse = resp
        if resp.status_code == 200:
            self.serviceId = resp.json()['id']
            return resp.json()
        else:
            return False

    # TODO: should be separate class
    def regenerate(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/services/'+self.serviceId+'/keys/generate.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, cookies=self.context.cookies, data=json.dumps({}), verify=False, headers=headers)
        log.debug(resp.text)
        self.rawResponse = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def json(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/services.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            service = [x for x in resp.json() if x['id'] == self.serviceId]
            if len(service)>0:
                return service[0]
            else:
                return False

        else:
            return False

    def delete(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/services/'+self.serviceId+'.json'
        headers = {'Content-Type': 'application/json'}
        resp = requests.delete(url, cookies=self.context.cookies, data=json.dumps({}), verify=False, headers=headers)
        log.debug(resp.text)
        self.rawResponse = resp
        if resp.status_code == 200:
            #print resp.json()
            return True
        else:
            return False





