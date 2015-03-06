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

import time
import logging as log
import copy

import simplejson as json

from qubell.api.globals import ZONE_NAME, DEFAULT_ENV_NAME
from qubell.api.tools import lazyproperty
from qubell.api.private import exceptions, operations
from qubell.api.private.common import QubellEntityList, Entity
from qubell.api.provider.router import ROUTER as router

__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__email__ = "vkhomenko@qubell.com"


class Environment(Entity):
    # noinspection PyShadowingBuiltins
    def __init__(self, organization, id):
        self.organization = organization
        self.organizationId = self.organization.organizationId
        self.environmentId = self.id = id

    @lazyproperty
    def zoneId(self):
        return self.json()['backend']

    @lazyproperty
    def services(self):
        from qubell.api.private.instance import InstanceList

        return InstanceList(list_json_method=self.list_services_json, organization=self)

    @property
    def name(self):
        return self.json()['name']

    @property
    def isDefault(self):
        return self.json()['isDefault']

    def __getattr__(self, key):
        resp = self.json()
        if key not in resp:
            raise exceptions.NotFoundError('Cannot get property %s' % key)
        return resp[key] or False

    @staticmethod
    def new(organization, name, zone_id=None, default=False):
        log.info("Creating environment: %s" % name)
        if not zone_id:
            zone_id = organization.zone.zoneId
        data = {'isDefault': default, 'name': name, 'backend': zone_id, 'organizationId': organization.organizationId}
        log.debug(data)
        resp = router.post_organization_environment(org_id=organization.organizationId, data=json.dumps(data)).json()
        env = Environment(organization, id=resp['id'])
        log.info("Environment created: %s (%s)" % (name, env.environmentId))
        return env

    # noinspection PyUnusedLocal
    def restore(self, config, clean=False, timeout=10):
        config = copy.deepcopy(config)
        with self as env:
            if clean:
                env.clean()
            for marker in config.pop('markers', []):
                env.add_marker(marker)
            for policy in config.pop('policies', []):
                env.add_policy(policy)
            for prop in config.pop('properties', []):
                env.add_property(**prop)
            for service in config.pop('services', []):
                instance = self.organization.get_instance(id=service.pop('id', None), name=service.pop('name'))
                env.add_service(instance)
        for service in self.services:
            service.running()

    def json(self):
        return router.get_environment(org_id=self.organizationId, env_id=self.environmentId).json()

    def delete(self):
        router.delete_environment(org_id=self.organizationId, env_id=self.environmentId)
        return True

    def set_as_default(self):
        data = json.dumps({'environmentId': self.id})
        return router.put_organization_default_environment(org_id=self.organizationId, data=data).json()

    def list_available_services_json(self):
        return router.get_environment_available_services(org_id=self.organizationId, env_id=self.environmentId).json()

    def list_services_json(self):
        return self.json()['services']

    def _put_environment(self, data):
        # We could get 500 error here, if tests runs in parallel or strategy is not active
        try:
            return router.put_environment(org_id=self.organizationId, env_id=self.environmentId, data=data)
        except exceptions.ApiError:
            from random import randint

            time.sleep(randint(1, 10))
            return router.put_environment(org_id=self.organizationId, env_id=self.environmentId, data=data)

    # Operations

    def add_service(self, service):
        with self as env:
            env.add_service(service)

    def remove_service(self, service):
        with self as env:
            env.remove_service(service)

    def add_marker(self, marker):
        with self as env:
            env.add_marker(marker)

    def remove_marker(self, marker):
        with self as env:
            env.remove_marker(marker)

    # noinspection PyShadowingBuiltins
    def add_property(self, name, type, value):
        with self as env:
            env.add_property(name, type, value)

    set_property = add_property

    def remove_property(self, name):
        with self as env:
            env.remove_property(name)

    def clean(self):
        with self as env:
            env.clean()

    def add_policy(self, new):
        with self as env:
            env.add_policy(new)

    def remove_policy(self, policy_name):
        with self as env:
            env.remove_policy(policy_name)

    def __bulk_update(self, env_operations):

        def clean():
            data['serviceIds'] = []
            data['services'] = []
            log.info("Cleaning environment %s (%s)" % (self.name, self.id))

        # todo: allow add policy via action-parameter-value
        def add_policy(new):
            data['policies'].append(new)
            log.info("Adding policy %s.%s to environment %s (%s)" % (
                new.get('action'), new.get('parameter'), self.name, self.id))

        # noinspection PyUnusedLocal
        def remove_policy(policy_name):
            raise NotImplementedError

        def add_service(service):
            if service.instanceId not in data['serviceIds']:
                data['serviceIds'].append(service.instanceId)
                data['services'].append(service.json())
                log.info("Adding service %s (%s) to environment %s (%s)" %
                         (service.name, service.id, self.name, self.id))

            if service.is_secure_vault:
                user_data = service.userData
                if 'defaultKey' in user_data:
                    key = user_data['defaultKey']
                else:
                    key = service.regenerate()['id']

                add_policy({"action": "provisionVms", "parameter": "publicKeyId", "value": key})

        def remove_service(service):
            data['serviceIds'].remove(service.instanceId)
            data['services'] = [s for s in data['services'] if s['id'] != service.id]
            log.info("Removing service %s (%s) from environment %s (%s)" %
                     (service.name, service.id, self.name, self.id))

        # noinspection PyShadowingBuiltins
        def add_property(name, type, value):
            data['properties'].append({'name': name, 'type': type, 'value': value})
            log.info("Adding property %s to environment %s (%s)" % (name, self.name, self.id))

        def remove_property(name):
            prop = [p for p in data['properties'] if p['name'] == name]
            if len(prop) < 1:
                log.error('Unable to remove property %s. Not found.' % name)
            data['properties'].remove(prop[0])
            log.info("Removing property %s from environment %s (%s)" % (name, self.name, self.id))

        def add_marker(marker):
            data['markers'].append({'name': marker})
            log.info("Adding marker %s to environment %s (%s)" % (marker, self.name, self.id))

        def remove_marker(marker):
            data['markers'].remove({'name': marker})
            log.info("Removing marker %s from environment %s (%s)" % (marker, self.name, self.id))

        actions = dict(clean=clean, add_policy=add_policy, remove_policy=remove_policy, add_marker=add_marker,
                       remove_marker=remove_marker, add_property=add_property, remove_property=remove_property,
                       add_service=add_service, remove_service=remove_service)

        data = self.json()
        for operation in env_operations:
            action, args, kwargs = operation
            actions[action](*args, **kwargs)
        return self._put_environment(data=json.dumps(data)).json()

    # noinspection PyMethodMayBeStatic
    def set_backend(self, zone):
        raise exceptions.ApiError("Change environment backend is not supported, since 24.x")

    def __enter__(self):
        """
        :rtype: EnvironmentOperations
        """
        self.__bulk = EnvironmentOperations()
        return self.__bulk

    # noinspection PyShadowingBuiltins,PyUnusedLocal
    def __exit__(self, type, value, traceback):
        self.__bulk.invalidate()
        self.__bulk_update(self.__bulk.operations)


class EnvironmentList(QubellEntityList):
    base_clz = Environment

    @property
    def default(self):
        """
            Returns environment marked as default.
            When Zone is set marked default makes no sense, special env with proper Zone is returned.
        """
        if ZONE_NAME:
            log.info("Getting or creating default environment for zone with name '{0}'".format(DEFAULT_ENV_NAME()))
            zone_id = self.organization.zones[ZONE_NAME].id
            return self.organization.get_or_create_environment(name=DEFAULT_ENV_NAME(), zone=zone_id)

        def_envs = [env_j["id"] for env_j in self.json() if env_j["isDefault"]]

        if len(def_envs) > 1:
            log.warning('Found more than one default environment. Picking last.')
            return self[def_envs[-1]]
        elif len(def_envs) == 1:
            return self[def_envs[0]]
        raise exceptions.NotFoundError('Unable to get default environment')


@operations()
class EnvironmentOperations(object):
    def add_policy(self, policy):
        pass

    def remove_policy(self, policy_name):
        pass

    def add_marker(self, marker):
        pass

    def remove_marker(self, marker):
        pass

    # noinspection PyShadowingBuiltins
    def add_property(self, name, type, value):
        pass

    def remove_property(self, name):
        pass

    def add_service(self, service):
        pass

    def remove_service(self, service):
        pass

    def clean(self):
        pass
