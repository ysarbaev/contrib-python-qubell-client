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
import simplejson as json
import logging as log
import qubellclient.tools as tools
from qubellclient.private.platform import QubellPlatform

class Organization(QubellPlatform):

    rawResponse = None

    def __init__(self, context, id=None, name=None):
        self.context = context
        self.name = name or "test-org-"+tools.rand()

        # Create org
        if not id:
            self.organizationId = self._create()['id']
        # Or use existing
        else:
            self.organizationId = id

        self.context.organizationId = self.organizationId

        self.zoneId = self.getZones()[0]['id'] #TODO
        self.context.zoneId = self.zoneId

    def _create(self):
        log.info("Creating organization: %s" % self.name)
        url = self.context.api+'/organizations.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'editable': 'true',
                              'name': self.name})
        resp = requests.post(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawResponse = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def json(self):
        url = self.context.api+'/organizations.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

    def application(self, *args, **kwargs):
        from application import Application
        return Application(self.context, *args, **kwargs)

    def service(self, *args, **kwargs):
        from service import Service
        return Service(self.context, *args, **kwargs)

    def environment(self, *args, **kwargs):
        from environment import Environment
        return Environment(self.context, *args, **kwargs)

    def provider(self, *args, **kwargs):
        from provider import Provider
        return Provider(self.context, *args, **kwargs)

    def getZones(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/zones.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False
