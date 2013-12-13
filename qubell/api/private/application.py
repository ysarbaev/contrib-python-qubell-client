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

from qubell.api.private.organization import Organization
from qubell.api.private import exceptions, instance, revision


class Application(Organization):
    """
    Base class for applications. It should create application and services+environment requested
    """
    rawResponse = None

    def __parse(self, values):
        ret = {}
        for val in values:
            ret[val['id']] = val['value']
        return ret

    def __init__(self, context, id):
        self.context = context
        self.applicationId = id
        self.context.applicationId = id

        my = self.json()
        self.name = my['name']
        self.manifest = my['manifest']

    def delete(self):
        log.info("Removing application: %s" % self.name)
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'.json'
        resp = requests.delete(url, verify=False, cookies=self.context.cookies)
        log.debug(resp.text)
        if resp.status_code == 200:
            return True
        else:
            return False

    def clean(self):
        instances = self.instances
        if instances:
            for ins in instances:
                obj = instance.Instance(context=self.context, id=ins['id'])
                st = obj.status
                if st not in ['Destroyed', 'Destroying', 'Launching', 'Executing']: # Tests could fail and we can get any statye here
                    log.info("Destroying instance %s" % obj.name)
                    obj.delete()
                    assert obj.destroyed(timeout=10)

        revisions = self.revisions
        if revisions:
            for rev in revisions:
                obj = revision.Revision(context=self.context, id=rev['id'])
                obj.delete()
        return True

    def json(self, key=None):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'.json'
        resp = requests.get(url, cookies=self.context.cookies, data="{}", verify=False)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        raise exceptions.ApiError('Unable to get application by url %s\n, got error: %s' % (url, resp.text))

    def __getattr__(self, key):
        resp = self.json()
        if not resp.has_key(key):
            raise exceptions.NotFoundError('Cannot get property %s' % key)
        return resp[key] or False

    def upload(self, manifest):
        log.info("Uploading manifest")
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'/manifests.json'
        resp = requests.post(url, files={'path': manifest.content}, data={'manifestSource': 'upload', 'name': self.name}, verify=False, cookies=self.context.cookies)
        log.debug(resp.text)

        self.rawResponse = resp
        if resp.status_code == 200:
            self.manifest = manifest
            return resp.json()
        else:
            log.error('Cannot upload manifest: %s' % resp.content)
            return False

    def launch(self, **argv):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'/launch.json'
        headers = {'Content-Type': 'application/json'}
        if not 'environmentId' in argv.keys():
            argv['environmentId'] = self.context.environmentId
        data = json.dumps(argv)
        resp = requests.post(url, cookies=self.context.cookies, data=data, verify=False, headers=headers)

        log.debug('--- APPLICATION LAUNCH REQUEST ---')
        log.debug('REQUEST HEADERS: %s' % resp.request.headers)
        log.debug('REQUEST: %s' % resp.request.body)
        log.debug('RESPONSE: %s' % resp.text)

        self.rawResponse = resp
        if resp.status_code == 200:
            instance_id = resp.json()['id']
            return self.get_instance(instance_id)
        else:
            log.error('Unable to launch instance: %s' % resp.content)
            return False

    def get_instance(self, id):
        from qubell.api.private.instance import Instance
        return Instance(context=self.context, id=id)

    def delete_instance(self, id):
        ins = self.get_instance(id)
        return ins.delete()

    def get_revision(self, id):
        from qubell.api.private.revision import Revision
        self.context.applicationId = self.applicationId
        return Revision(context=self.context, id=id)

    def list_revisions(self):
        return self.revisions()

    def create_revision(self, name, instance, parameters=[], version=None):
        if not version:
            version=self.get_manifest()['version']
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'/revisions.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({ 'name': name,
                    'parameters': parameters,
                    'submoduleRevisions': {},
                    'returnValues': [],
                    'applicationId': self.applicationId,
                    'applicationName': self.name,
                    'version': version,
                    'instanceId': instance.instanceId})
        resp = requests.post(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        if resp.status_code==200:
            return self.get_revision(id=resp.json()['id'])
        raise exceptions.ApiError('Unable to get revision, got error: %s' % resp.text)

    def delete_revision(self, id):
        rev = self.get_revision(id)
        rev.delete()

    def get_manifest(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'/refreshManifest.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({})
        resp = requests.post(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            return resp.json()
        else:
            return False
