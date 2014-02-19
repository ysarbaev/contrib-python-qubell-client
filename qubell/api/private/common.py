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
__version__ = ""
__email__ = "vkhomenko@qubell.com"


from qubell.api.private import exceptions

class Qubell_object_list(object):
    """ Class to store qubell objects information (Instances, Applications, etc)
    Class should give convenient way for searching and manipulating objects
    """

    def __init__(self, organization):
        self.organization = organization
        self.auth = self.organization.auth
        self.organizationId = self.organization.organizationId
        self.object_list = []
        self.__generate_object_list()

    def __iter__(self):
        i = 0
        while i<len(self.object_list):
            yield self.object_list[i]
            i+=1

    def __len__(self):
        return len(self.object_list)

    def __repr__(self):
        return str(self.object_list)

    def __getitem__(self, item):
        # TODO: Guess item is ID or name
        found = [x for x in self.object_list if x.name == item]
        if len(found)>0:
            return found[-1]
        raise exceptions.NotFoundError('Unable to get instance by name')

    def __contains__(self, item):
        return item in self.object_list

    def add(self, item):
        self.object_list.append(item)

    def remove(self, item):
        self.object_list.remove(item)

    def __generate_object_list(self):
        pass