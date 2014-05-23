Python-qubell-client
====================

Repository contains:


qubell/api/private - library to access qubell via dev (non-stable) api.

stories - tests in python unittests format. Primary goal is to test qubell platform functionality


Pre-requisites
==============

- python2.7 or greater
- requests
- yaml
- testtools
- nose or pytest

```bash
sudo pip install -r requirements.txt
```
or

```bash
sudo easy_install `cat requirements.txt`
```

Configuration
=============

To configure tests, set up environment variables:
QUBELL_USER, QUBELL_PASSWORD - user to access qubell
QUBELL_TENANT - url to qubell platform (https://express.qubell.com)
QUBELL_ORGANIZATION - name of organization to use. Will be created if not exists.

If you attend to create environment, you will also need:

PROVIDER_TYPE, PROVIDER_REGION, PROVIDER_IDENTITY, PROVIDER_CREDENTIAL - credentials for amazon ec2. (to create provider)
By default Amazon ec2 used (in us-east zone)

Example:
```bash
export QUBELL_TENANT="https://express.qubell.com"
export QUBELL_USER="user@gmail.com"
export QUBELL_PASSWORD="password"
export QUBELL_ORGANIZATION="my-org"

# Additional parameters
export PROVIDER_TYPE="aws-ec2"
export PROVIDER_REGION="us-east-1"
export PROVIDER_IDENTITY="FFFFFFFFF"
export PROVIDER_CREDENTIAL="FFFFFFFFFF"
```


Running tests
=============

Run single test::
```bash
nosetests -s -v stories.instance.test_actions:BasicInstanceActionsTest.test_workflow_launch
```

Run all tests::
```bash
nosetests -s -v stories
```

or just::
```bash
nosetests
```

If you need special environment to run your test, you can use restore_env.py script (see lime project).


Using client
============


Building sandboxes
------------------

Sandboxes in qubell platform could be created on different levels. Maximum isolated sandbox could be achieved by separate organization (with it's own environments, users and application).

Simple way to create sandbox (see ./contrib-python-qubell-client/sandbox/):
Create file containing organization structure:

cat default.env
```bash
organizations:
- name: DEFAULT_ORG
  applications:
  - name: super_parent
    file: ./super_parent.yml
  - name: middle_child
    file: ./middle_child.yml
  - name: child
    file: ./child.yml

  environments:
  - name: default
    services:
    - name: Default credentials service
    - name: Default workflow service
    - name: child-service

  services:
  - name: Default workflow service
    type: builtin:workflow_service
  - name: Default credentials service
    type: builtin:cobalt_secure_store
  - name: child-service
    application: child

  instances:
  - name: test-instance
    application: super_parent
```

Run script:
```bash
./restore_env.py default.env
```

After, you will have fully configured organization, even with running instances. This example shows how to describe 3-level hearchical application, where child instance launched as service.

Note: do not forget to set up environment variables described before.


Coding your own scripts
-----------------------

First way of creating sandbox, using restore method:


```python
config="""
{'organizations': [{'name': 'DEFAULT_ORG',
                    'applications': [{'file': './super_parent.yml',
                                      'name': 'super_parent'},
                                     {'file': './middle_child.yml',
                                      'name': 'middle_child'},
                                     {'file': './child.yml',
                                      'name': 'child'}],
                    'environments': [{'name': 'default',
                                      'services': [{'name': 'Default credentials service'},
                                                   {'name': 'Default workflow service'},
                                                   {'name': 'child-service'}]}],
                    'instances': [{'application': 'super_parent',
                                   'name': 'test-instance'}],
                    'providers': [{'ec2SecurityGroup': 'default',
                                   'jcloudsCredential': 'AAAAAAAAA',
                                   'jcloudsIdentity': 'BBBBBBBBBBB',
                                   'jcloudsRegions': 'us-east-1',
                                   'name': 'generated-provider-for-tests',
                                   'provider': 'aws-ec2',
                                   'providerCopy': 'aws-ec2'}],
                    'services': [{'name': 'Default workflow service',
                                  'type': 'builtin:workflow_service'},
                                 {'name': 'Default credentials service',
                                  'type': 'builtin:cobalt_secure_store'},
                                 {'application': 'child',
                                  'name': 'child-service'}]}]}
"""

from qubell.api.private.platform import QubellPlatform

platform = QubellPlatform()
platform.connect(user="tester@qubell.com", password="password", tenant="https://api.qubell.com")

platform.restore(config)

# Let's check what we've got
print platform.organizations['DEFAULT_ORG'].name
for ins in platform.organizations['DEFAULT_ORG'].instances:
    print ins.name
```


Second way, using get/create methods:


##### Organization

Creating organization is simple::
```python
from qubell.api.private.platform import QubellPlatform

platform = QubellPlatform()
platform.connect(user="tester@qubell.com", password="password", tenant="https://api.qubell.com")

org = platform.organization(name="test-org")
```
After executing this code, organization "test-org" would be created (if not exists) or initialized (if exists)

Here is equivalent code:
```python
try:
    org = platform.get_organization(id="123")
except:
    org = platform.create_organization(name="test-org")
```


##### Environment

Usual environment consists of cloud account, keystore service and workflow service. So, we need to add these services to our organization, then add them to our environmen:

```python
access = {
  "provider": "aws-ec2",
  "usedEnvironments": [],
  "ec2SecurityGroup": "default",
  "providerCopy": "aws-ec2",
  "name": "test-provider",
  "jcloudsIdentity": KEY,
  "jcloudsCredential": SECRET_KEY,
  "jcloudsRegions": "us-east-1"
}

def prepare_env(org):

    # Add services to organization
    key_service = org.service(type='builtin:cobalt_secure_store', name='Default credentials service')
    wf_service = org.service(type='builtin:workflow_service', name='Default workflow service')
    prov = org.provider(access)

    # Add services to environment
    env = org.environment(name='new-environment')
    env.clean()
    env.add_service(key_service)
    env.add_service(wf_service)
    env.add_provider(prov)

    # Here we regenerate keypair
    env.add_policy(
        {"action": "provisionVms",
         "parameter": "publicKeyId",
         "value": key_service.regenerate()['id']})
    return org

prepare_env(org)
```

Now, platform ready to be used. We need only application with valid manifest.

##### Application

We need manifest to create application::

```python
manifest = Manifest(url="https://raw.github.com/qubell/contrib-python-qubell-client/master/qm/hierarchical-main.yml")

# Creating application
app = org.application(manifest=manifest, name='first_app')
```
or
```python
try:
    app = org.get_application(id="111")
except:
    org.create_application(manifest=manifest, name='first_app')
```

Application would be crated.
To launch it, use code::

```python
instance = org.launch(application=app)

# This way we wait instance to came up in 15 minutes or break.
assert instance.ready(15)
```
