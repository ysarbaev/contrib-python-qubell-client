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

class Provider(Organization):
    rawResponse = None

    def __init__(self, context, parameters, id=None):
        self.context = context
        self.__dict__.update(parameters)

        # Use existing
        if id:
            self.providerId = id

        # Or create
        else:
            payload = json.dumps(parameters)

            url = self.context.api+'/organizations/'+self.context.organizationId+'/providers.json'
            headers = {'Content-Type': 'application/json'}
            resp = requests.post(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
            log.debug(resp.text)

            self.rawResponse = resp
            if resp.status_code == 200:
                self.providerId = resp.json()['id']
                # Regenerate key when new keystore added
            else:
                return False