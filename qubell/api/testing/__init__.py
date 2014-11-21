
import logging as log

from qubell.api.private.platform import QubellPlatform
from qubell.api.private.testing import BaseTestCase as SandBoxTestCase, environment, instance, values, workflow
from qubell.api.globals import QUBELL as qubell_config, PROVIDER as cloud_config


platform = QubellPlatform.connect(
                tenant=qubell_config['tenant'],
                user=qubell_config['user'],
                password=qubell_config['password'])
log.info('Authentication succeeded.')


class BaseComponentTestCase(SandBoxTestCase):
    parameters = dict(qubell_config.items() + cloud_config.items())
    apps = []

    @classmethod
    def environment(cls, organization):
        base_env = super(BaseComponentTestCase, cls).environment(organization)
        base_env['applications'] = cls.apps
        return base_env

    @classmethod
    def setUpClass(cls):
        cls.platform = platform
        super(BaseComponentTestCase, cls).setUpClass()