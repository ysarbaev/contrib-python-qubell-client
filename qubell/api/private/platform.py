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

import logging as log

import requests
import simplejson as json

from qubell.api.private import exceptions


class QubellPlatform(object):


    def __init__(self, context, *args, **kwargs):
        self.context = context

    def authenticate(self):
        url = self.context.api+'/signIn'
        data = {
            'email': self.context.user,
            'password': self.context.password}
        # Use session to eliminate accidental falls
        rsession = requests.Session()
        rsession.post(url=url, data=data, verify=False)
        self.context.cookies = rsession.cookies
        rsession.close()
        if 'PLAY_SESSION' in self.context.cookies:
            return True
        else:
            return False

    def get_context(self):
        return self.context

    def create_organization(self, name):
        log.info("Creating organization: %s" % name)
        url = self.context.api+'/organizations.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'editable': 'true',
                              'name': name})
        resp = requests.post(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code == 200:
            return self.get_organization(resp.json()['id'])
        raise exceptions.ApiError('Unable to create organization %s, got error: %s' % (name, resp.text))

    def get_organization(self, id):
        log.info("Picking organization: %s" % id)
        from qubell.api.private.organization import Organization
        return Organization(self.context, id=id)

    def organization(self, id=None, name=None):
        """ Smart object. Will create organization or pick one, if exists"""
        if name:
            orgz = [org for org in self.list_organizations() if org['name'] == name]
            # Org found by name
            if len(orgz):
                return self.get_organization(orgz[0]['id'])
            else:
                return self.create_organization(name)
        else:
            name = 'generated-org-name'
            if id:
                return self.get_organization(id)
            else:
                return self.create_organization(name)

    def list_organizations(self):
        url = self.context.api+'/organizations.json'
        resp = requests.get(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get organizations list, got error: %s' % resp.text)


    def rename_organization(self):
        raise NotImplementedError

    def delete_organization(self):
        raise NotImplementedError('Api does not support organization deletion')


class Context(object):
    def __init__(self, user, password, api):
        self.user = user
        self.password = password
        self.api = api