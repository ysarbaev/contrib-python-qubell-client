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
import logging as log
import warnings

import simplejson as json

from qubell.api.provider.router import Router
from qubell import deprecated

#todo: understood, that some people may use this object for authentication, need to move this to proper place
from qubell.api.private.common import Auth
Auth = Auth # Auth usage, to be sure won't be removed from imports

__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__email__ = "vkhomenko@qubell.com"


class QubellPlatform(object):
    def __init__(self, auth=None, context=None):
        if context:
            warnings.warn("replace context with auth name, it is deprecated and will be removed", DeprecationWarning,
                          stacklevel=2)

        self.organizations = []
        self.auth = auth or context
        self.user = self.auth.user
        self.password = self.auth.password
        self.tenant = self.auth.tenant

        self.router = Router(self.tenant)


    def authenticate(self):
        self.router.connect(self.auth.user, self.auth.password)
        #todo: remove following, left for compatibility
        self.auth.cookies = self.router._cookies
        return True

    def create_organization(self, name):
        log.info("Creating organization: %s" % name)
        payload = json.dumps({'editable': 'true',
                              'name': name})
        resp = self.router.post_organization(data=payload)
        return self.get_organization(resp.json()['id'])


    def get_organization(self, id):
        log.info("Picking organization: %s" % id)
        from qubell.api.private.organization import Organization

        org = Organization(self.auth, id=id)
        self.organizations.append(org)
        return org

    def get_or_create_organization(self, id=None, name=None):
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

    def organization(self, id=None, name=None):
        """ Smart object. Will create organization, modify or pick one"""
        # TODO: Modify if parameters differs
        return self.get_or_create_organization(id, name)

    def organizations_json(self):
        resp = self.router.get_organizations()
        return resp.json()

    list_organizations = organizations_json

    def organizations(self):
        return OrganizationList(self.organizations_json())

    def restore(self, config):
        for org in config.pop('organizations', []):
            restored_org = self.get_or_create_organization(id=org.get('id'), name=org.get('name'))
            restored_org.restore(org)

    @deprecated
    def get_context(self):
        return self.auth