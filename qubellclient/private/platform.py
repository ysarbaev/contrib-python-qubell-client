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


    def getContext(self):
        return self.context


    def organization(self, *args, **kwargs):
        from qubellclient.private.organization import Organization
        return Organization(self.context, *args, **kwargs)

class Context(object):
    def __init__(self, user, password, api):
        self.user = user
        self.password = password
        self.api = api