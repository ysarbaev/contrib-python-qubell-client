====================
Python-qubell-client
====================

Repository contains:

qubellclient/private - library to access qubell via dev api.

qubellclient/tests - tests in python unittests format. Primary goal is to test qubell platform functionality using different api's (now only private)


Pre-requisites
==============

- python2.7 or greater
- requests
- yaml
- testtools
- nose

::

    sudo pip install -r requirements.txt
or

::

    sudo easy_install `cat requirements.txt`
    

Configuration
=============

To configure tests, set up environment variables:
QUBELL_USER, QUBELL_PASSWORD - user to access qubell
QUBELL_API - url to qubell platform
QUBELL_ORG - name of organization to use. Will be created if not exists.

PROVIDER, REGION, JCLOUDS_IDENTITY, JCLOUDS_CREDENTIALS - credentials for amazon ec2. (will create provider)
QUBELL_NEW - if you want to create new environment while tests run

::

	export QUBELL_API="http://qubell.com"
	export QUBELL_USER="user@gmail.com"
	export QUBELL_PASSWORD="password"
	export QUBELL_ORG="my-org"

	export JCLOUDS_IDENTITY="FFFFFFFFF"
	export JCLOUDS_CREDENTIALS="FFFFFFFFFF"


Running tests
=============

Run single test::

    nosetests -s -v qubellclient.tests.instance.test_actions:BasicInstanceActionsTest.test_actions

Run all tests::

    nosetests -s -v qubellclient/tests/

or just::

    nosetests



Using client
============

Create environment
__________________
Working example could be found in qubellclient/create_env.py. To use it, setup environment variables (see below) and run it::

	python qubellclient/create_env.py 


Building sandboxes
__________________
Sandboxes in qubell platform could be created on different levels. Maximum isolated sandbox could be achieved by separate organization (with it's own environments, users and application). 

Organization
____________
Creating organization is simple::

	from qubellclient.private.platform import QubellPlatform, Context

	context = Context(user="tester@qubell.com", password="password", api="https://api.qubell.com")
	platform = QubellPlatform(context=context)
	org = platform.organization(name="test-org")

After executing this code, organization "test-org" would be created (if not exists) or initialized (if exists)

Now we need to create environment in organization.

Environment
___________

Usual environment consists of cloud account, keystore service and workflow service. So, we need to add theese services to our organization, then add them to our environment. By default we use "default" environment::

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
	    key_service = org.service(type='builtin:cobalt_secure_store', name='Keystore')
	    wf_service = org.service(type='builtin:workflow_service', name='Workflow', parameters='{}')
	    prov = org.provider(access)

	    # Add services to environment
	    env = org.environment(name='default')
	    env.clean()
	    env.serviceAdd(key_service)
	    env.serviceAdd(wf_service)
	    env.providerAdd(prov)

	    # Here we regenerate keypair
	    env.policyAdd(
	        {"action": "provisionVms",
	         "parameter": "publicKeyId",
	         "value": key_service.regenerate()['id']})

	    return org.organizationId

	prepare_env(org)


Now, platform ready to be used. We need only application with valid manifest.

Application
___________
We need manifest to create application::

	manifest = Manifest(url="https://raw.github.com/qubell/contrib-python-qubell-client/master/qm/hierarchical-main.yml")

	# Creating application
	app = org.application(manifest=manifest, name='first_app')


Application would be crated.
To launch it, use code::

	instance = app.launch()

	# This way we wait instance to came up in 15 minutes or break.
	assert instance.ready(15)


