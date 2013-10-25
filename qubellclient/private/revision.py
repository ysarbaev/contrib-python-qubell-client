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
import application
import requests
import simplejson as json
from qubellclient.tools import retry



class Revision(application.Application):
    """
    Base class for revision
    """
    rawRespose = None

    def __init__(self, context, name=None, id=None):
        if id: self.revisionId = id
        self.context = context
        if name: self.name = name

    def delete(self):
        url = self.context.api+'/organizations/'+self.context.organizationId+'/applications/'+self.context.applicationId+'/revisions/'+self.revisionId+'.json'
        resp = requests.delete(url, cookies=self.context.cookies, verify=False)
        log.debug(resp.text)
        self.rawRespose = resp
        if resp.status_code==200:
            return True
        else:
            return False
