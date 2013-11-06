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
from qubellclient.private.organization import Organization
import qubellclient.tools as tools

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

    def __init__(self, context, id=None, manifest=None, name=None):
        self.context = context
        self.name = name or "test-app-"+tools.rand()
        self.manifest = manifest

        # Create application
        if not id:
            newapp = self._create()
            assert newapp
            self.applicationId = newapp['id']
        # Use existing app
        else:
            self.applicationId = id
        self.context.applicationId = self.applicationId

    def _create(self):
        log.info("Creating application: %s" % self.name)
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications.json'
        resp = requests.post(url, files={'path': self.manifest.content}, data={'manifestSource': 'upload', 'name': self.name}, verify=False, cookies=self.context.cookies)
        log.debug(resp.text)
        if resp.status_code == 200:
            return resp.json()
        else:
            return False

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
        import instance
        if instances:
            for ins in instances:
                obj = instance.Instance(context=self.context, id=ins['id'])
                st = obj.status
                if st not in ['Destroyed', 'Destroying', 'Launching', 'Executing']: # Tests could fail and we can get any statye here
                    log.info("Destroying instance %s" % obj.name)
                    obj.delete()
                    assert obj.destroyed(timeout=10)

        revisions = self.revisions
        import revision
        if revisions:
            for rev in revisions:
                obj = revision.Revision(context=self.context, id=rev['id'])
                obj.delete()
        return True


    def json(self, key=None):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'.json'
        resp = requests.get(url, cookies=self.context.cookies, data="{}", verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code == 200:
            # return same way public api does
#            if key and (key in ['instances', 'environments']):
#                return self.__parse(resp.json()[key])
#            else:
#                return resp.json()[key]
            return resp.json()
        else:
            return None

    def __getattr__(self, key):
        resp = self.json()
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
        data = json.dumps(argv)
        resp = requests.post(url, cookies=self.context.cookies, data=data, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawResponse = resp
        if resp.status_code == 200:
            instance_id = resp.json()['id']
            from qubellclient.private.instance import Instance
            return Instance(context=self.context, id=instance_id)
        else:
            log.error('Unable to launch instance: %s' % resp.content)
            return False

    def revisionCreate(self, name, instance, parameters=[], version=None):
        if not version:
            version=self.getManifest()['version']
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.applicationId+'/revisions.json'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({ 'name': name,
                    'parameters': parameters,
                    'submoduleRevisions': {},
                    'returnValues': [],
                    'applicationId': self.context.applicationId,
                    'applicationName': "api",
                    'version': version,
                    'instanceId': instance.instanceId})
        resp = requests.post(url, cookies=self.context.cookies, data=payload, verify=False, headers=headers)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code==200:
            import revision
            return revision.Revision(context=self.context, name=name, id=resp.json()['id'])
        else:
            return False

    def getManifest(self):
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
