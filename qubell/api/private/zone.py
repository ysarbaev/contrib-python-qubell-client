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

from qubell.api.private import exceptions


class Zone(object):
    def __init__(self, auth, organization, id):
        self.auth = auth
        self.zoneId = id
        self.organization = organization
        my = self.json()
        self.name = my['name']

    def __getattr__(self, key):
        resp = self.json()
        if resp.has_key(key):
            return resp[key]
        raise exceptions.NotFoundError('Cannot get zone property %s' % key)


    def json(self):
        url = self.auth.api+'/organizations/'+self.organization.organizationId+'/zones.json'
        resp = requests.get(url, cookies=self.auth.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            zone = [x for x in resp.json() if x['id'] == self.zoneId]
            if len(zone)>0:
                return zone[0]
        raise exceptions.ApiError('Unable to get zones list, got error: %s' % resp.text)
