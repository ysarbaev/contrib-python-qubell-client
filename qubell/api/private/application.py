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
import simplejson as json

from qubell.api.private import exceptions
from qubell.api.private.common import EntityList
from qubell.api.provider.router import ROUTER as router


class Applications(EntityList):
    def __init__(self, organization):
        self.organization = organization
        self.auth = self.organization.auth
        self.organizationId = self.organization.organizationId
        EntityList.__init__(self)

    def _generate_object_list(self):
        for app in self.organization.list_applications_json():
            self.object_list.append(Application(self.auth, self.organization, id=app['id']))


class Application(object):
    """
    Base class for applications. It should create application and services+environment requested
    """

    def __update(self):
        info = self.json()
        self.name = info['name']
        self.id = self.applicationId
        self.defaultEnvironment = self.organization.get_default_environment()


    def __init__(self, auth, organization, **kwargs):
        if hasattr(self, 'applicationId'):
            log.warning("Application reinitialized. Dangerous!")
        self.revisions = []
        self.auth = auth
        self.organization = organization
        self.organizationId = self.organization.organizationId
        self.defaultEnvironment = self.organization.get_default_environment()
        if 'id' in kwargs:
            self.applicationId = kwargs.get('id')
            self.__update()

    def __parse(self, values):
        ret = {}
        for val in values:
            ret[val['id']] = val['value']
        return ret

        #TODO: Think how to restore revisions

    def create(self, name, manifest):
        log.info("Creating application: %s" % name)
        resp = router.post_organization_application(org_id=self.organizationId, files={'path': manifest.content}, data={'manifestSource': 'upload', 'name': name})
        self.applicationId = resp.json()['id']
        self.manifest = manifest
        self.__update()
        return self

    def delete(self):
        log.info("Removing application: %s" % self.name)
        router.delete_application(org_id=self.organizationId, app_id=self.applicationId)
        return True

    def update(self, **kwargs):
        if kwargs.get('manifest'):
            self.upload(kwargs.pop('manifest'))
        log.info("Updating application: %s" % self.name)

        data = json.dumps(kwargs)
        resp = router.post_application(org_id=self.organizationId, app_id=self.applicationId, data=data)
        self.__update() #todo: json called here
        return resp.json()

    def clean(self, timeout=3):
        for ins in self.instances:
            st = ins.status
            if st not in ['Destroyed', 'Destroying', 'Launching', 'Executing']: # Tests could fail and we can get any statye here
                log.info("Destroying instance %s" % ins.name)
                ins.delete()
                assert ins.destroyed(timeout=timeout)
                self.instances.remove(ins)

        for rev in self.revisions:
            self.revisions.remove(rev)
            rev.delete()
        return True

    def json(self):
        return router.get_application(org_id=self.organizationId, app_id=self.applicationId).json()

    def __getattr__(self, key):
        resp = self.json()
        if not resp.has_key(key):
            raise exceptions.NotFoundError('Cannot get property %s' % key)
        return resp[key] or False


# REVISION
    def get_revision(self, id):
        from qubell.api.private.revision import Revision
        rev = Revision(auth=self.auth, application=self, id=id)
        self.revisions.append(rev)
        return rev

    def list_revisions(self):
        return self.revisions()

    def create_revision(self, name, instance, parameters=[], version=None):
        if not version:
            version=self.get_manifest()['manifestVersion']
        payload = json.dumps({ 'name': name,
                    'parameters': parameters,
                    'submoduleRevisions': {},
                    'returnValues': [],
                    'applicationId': self.applicationId,
                    'applicationName': self.name,
                    'version': version,
                    'instanceId': instance.instanceId})
        resp = router.post_revision(org_id=self.organizationId, app_id=self.applicationId, data=payload)
        return self.get_revision(id=resp.json()['id'])

    def delete_revision(self, id):
        rev = self.get_revision(id)
        self.revisions.remove(rev.name)
        rev.delete()

# MANIFEST

    def get_manifest(self):
        return router.post_application_refresh(org_id=self.organizationId, app_id=self.applicationId).json()

    def upload(self, manifest):
        log.info("Uploading manifest")
        self.manifest = manifest
        return router.post_manifest(org_id=self.organizationId, app_id=self.applicationId,
                                    files={'path': manifest.content},
                                    data={'manifestSource': 'upload', 'name': self.name}).json()