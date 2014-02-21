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
import time

from qubell.api.tools import is_bson_id
from qubell.api.private import exceptions
from qubell import deprecated


__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__version__ = ""
__email__ = "vkhomenko@qubell.com"


class EntityList(object):
    """ Class to store qubell objects information (Instances, Applications, etc)
    Gives convenient way for searching and manipulating objects
    """

    def __init__(self):
        self.object_list = []
        self._generate_object_list()

    def __iter__(self):
        return iter(self.object_list)

    def __len__(self):
        return len(self.object_list)

    def __repr__(self):
        return str(self.object_list)

    def __getitem__(self, item):
        if isinstance(item, int) or isinstance(item, slice): return self.object_list[item]

        found = [x for x in self.object_list if (is_bson_id(item) and x.id == item) or x.name == item]
        if len(found) is 0:
            raise exceptions.NotFoundError("None of '{1}' in {0}".format(self.__class__.__name__, item))
        return found[-1]

    def __contains__(self, item):
        return item.id in [item.id for item in self.object_list]

    def add(self, item):
        self.object_list.append(item)

    def remove(self, item):
        self.object_list.remove(item)

    def _generate_object_list(self):
        raise AssertionError("'_generate_object_list' method should be implemented in subclasses")

#todo: what this object does?
class QubellEntityList(EntityList):
    """
    This is base class for entities that depends on organization
    """

    def __init__(self, list_json_method, organization):
        self.organization = organization
        self.auth = self.organization.auth
        self.organizationId = self.organization.organizationId
        self.json = list_json_method
        EntityList.__init__(self)

    # noinspection PyUnresolvedReferences
    def _generate_object_list(self):
        assert self.base_clz, "Define 'base_clz' in constructor or override this method"
        for ent in self.json():
            start = time.time()
            entity = self.base_clz(auth=self.auth, organization=self.organization, id=ent['id'])
            end = time.time()
            elapsed = int((end - start) * 1000.0)
            log.debug("  Listing Time: Fetching {0}='{name}' with id={id} took {elapsed} ms".format(self.base_clz.__name__,
                                                                                                 id=ent['id'],
                                                                                                 name=ent['name'],
                                                                                                 elapsed=elapsed))
            self.object_list.append(entity)



class Auth(object):
    @deprecated(msg="use global from qubell.api.provider.ROUTER as router instead")
    def __init__(self, user, password, tenant):
        self.user = user
        self.password = password
        self.tenant = tenant

        # TODO: parse tenant to generate api url
        self.api = tenant


class Context(Auth):
    @deprecated(msg="use global from qubell.api.provider.ROUTER as router instead")
    def __init__(self, user, password, api):
        Auth.__init__(self, user, password, api)
