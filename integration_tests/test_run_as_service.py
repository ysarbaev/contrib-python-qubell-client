import os
from integration_tests import base
from qubell.api.private.platform import QubellPlatform
from qubell.api.private.testing import environment, instance, values, BaseTestCase

def manifest(name):
    return os.path.realpath(os.path.join(os.path.dirname(__file__), name))

@environment({"default": {}})
class RunAsServiceTest(BaseTestCase):
    service_name = "service"
    client_name = "client"
    parameters = base.parameters
    platform = QubellPlatform.connect(parameters['tenant'], parameters['user'], parameters['pass'])

    apps = [
        {"name": client_name, "file": manifest("client.yml")},
        {"name": service_name, "file": manifest("service.yml"), "add_as_service": True}
    ]

    @classmethod
    def environment(cls, organization):
        base_env = super(RunAsServiceTest, cls).environment(cls.parameters['organization'])
        base_env['applications'] = cls.apps
        return base_env

    @instance(byApplication=client_name)
    @values({"serv.stringValue": "value"})
    def test_client_connected(self, instance, value):
        self.assertEqual(value, "hello")
