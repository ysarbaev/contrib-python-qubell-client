
====================
Python-qubell-client
====================

Repository contains:

qubellclient/private - library to access qubell via dev api.

qubellclient/tests - tests in python unittests format. Primary goal is to test qubell platform functionality using different api's (now only private)


Pre-requisites
--------------

- python2.7 or greater
- python-requests
- python-yaml
- python-nose
- python-testtools


Configuration
-------------

To configure tests, set up environment variables:
QUBELL_USER, QUBELL_PASSWORD - user to access qubell
QUBELL_API - url to qubell platform
QUBELL_ORG - name of organization to use. Will be created if not exists.

PROVIDER, REGION, JCLOUDS_IDENTITY, JCLOUDS_CREDENTIALS - credentials for amazon ec2. (will create provider)
QUBELL_NEW - if you want to create new environment while tests run


Running tests
-------------

Run single test:
 
    nosetests -s -v qubellclient.tests.instance.test_actions:InstanceTest.test_actions

Run all tests:
 
    nosetests -s -v qubellclient/tests/

or just:
 
    nosetests



Creating qubell environment
===========================

Sandboxes in qubell platform could be created on different levels. Maximum isolated sandbox could be achieved by separate organization (with it's own environments, users and application). 

Organization
------------
Creating organization is simple:

	from qubellclient.private.platform import QubellPlatform, Context

	context = Context(user="tester@qubell.com", password="password", api="https://api.qubell.com")
	platform = QubellPlatform(context=context)
	org = platform.organization(name="test-org")

After executing this code, organization "test-org" would be created (if not exists) or initialized (if exists)

Now we need to create environment in organization.

Environment
-----------

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
-----------
We need manifest to create application:

	manifest = Manifest(url="https://raw.github.com/qubell/docs/master/developer/examples/hierarchical-main.yml?login=vasichkin&token=19f0453adcc53ea22ff6def5d78bcf46")

	# Creating application
	app = org.application(manifest=manifest, name='first_app')


Application would be crated.
To launch it, use code:

	instance = app.launch()

	# This way we wait instance to came up in 15 minutes or break.
	assert instance.ready(15)


Writing tests
=============

We use python's unittests to create tests.
We have base class, where basic initialization made.

To add test, find existing test class that fits usecase or create new. 


Simple test looks like this:

	import os
	import qubellclient.tests.base as base
	from qubellclient.private.manifest import Manifest
	from qubellclient.tests.base import attr


	class BasicInstanceActionsTest(base.BaseTestCasePrivate):

	# Here we prepare environment once for all tests in class.
	    @classmethod
	    def setUpClass(cls):
	        # Call all parents setups
	        super(BasicInstanceActionsTest, cls).setUpClass()
	        # We create application for testclass
	        cls.app = cls.organization.application(name="%s-test-instance-actions" % cls.prefix, manifest=cls.manifest)

	# Here we cleaning our environment. Delete all created stuff
	    @classmethod
	    def tearDownClass(cls):
	        # Call all parents teardowns
	        super(BasicInstanceActionsTest, cls).tearDownClass()
	        # We must clean environment after tests
	        cls.app.delete()

	# This would be executed for each test
	# We create fresh instance for every test
	    def setUp(self):
	        super(BasicInstanceActionsTest, self).setUp()
	        self.app.upload(self.manifest)
	        self.instance = self.app.launch(destroyInterval=300000)

	        # Check instance launched and running
	        self.assertTrue(self.instance, "%s-%s: Instance failed to launch" % (self.prefix, self._testMethodName))
	        self.assertTrue(self.instance.ready(),"%s-%s: Instance not in 'running' state after timeout" % (self.prefix, self._testMethodName))

	# Also, clean after each test
	    def tearDown(self):
	        super(BasicInstanceActionsTest, self).tearDown()
	        self.assertTrue(self.instance.destroy())
	        self.assertTrue(self.instance.destroyed())


	# Tests
	    @attr('smoke')
	    def test_workflow_launch(self):
	        ''' We have instance launched by setUp. Now launch workflow there and check it works.
	        '''

	        self.assertEqual("This is default manifest", self.instance.returnValues['out.app_output'])
	        self.instance.runWorkflow(name='action.default')
	        self.assertTrue(self.instance.ready(), "%s-%s: Failed to execute workflow" % (self.prefix, self._testMethodName))
	        self.assertEqual('Action WF launched', self.instance.returnValues['out.app_output'])

Best practices:
---------------

- Every testclass should create it's own application. Use prefix in name as shown in example
- Use setUp and setUpClass for environment preparations. Test should only contain tested operations
- Do not forget to clean after tests
- The place where you create something is a good place to delete it. (if we create instance in test, delete it in test, not in teardown)
- Always check that operation succedded. You can get lot of false positives otherwise.
- Report as much as you can. It will make searching for fails easy.

Working tests and examples could be found in 'tests' directory.

