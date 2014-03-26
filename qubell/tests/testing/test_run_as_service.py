import os
from qubell.api.private.platform import QubellPlatform
from qubell.api.private.testing import environment, instance, values, BaseTestCase
from test_qubell_client import base

def manifest(name):
    return os.path.realpath(os.path.join(os.path.dirname(__file__), name))

@environment({"default": {}})
class RunAsServiceTest(BaseTestCase):
    service_name = "service"
    client_name = "client"
    platform = QubellPlatform.connect(base.tenant, base.user, base.password)
    platform.authenticate()
    parameters = {
        "organization": base.org,
        'provider_name': os.getenv('PROVIDER_NAME', "test-provider"),
        'provider_type': os.environ['PROVIDER_TYPE'],
        'provider_identity': os.environ['PROVIDER_IDENTITY'],
        'provider_credential': os.environ['PROVIDER_CREDENTIAL'],
        'provider_region': os.environ['PROVIDER_REGION']
    }
    apps = [
        {"name": client_name, "file": manifest("client.yml")},
        {"name": service_name, "file": manifest("service.yml"), "add_as_service": True}
    ]

    @classmethod
    def environment(cls, organization):
        base_env = super(RunAsServiceTest, cls).environment(base.org)
        base_env['applications'] = cls.apps
        return base_env

    @instance(byApplication=client_name)
    @values({"serv.stringValue": "value"})
    def test_client_connected(self, instance, value):
        self.assertEqual(value, "hello")
