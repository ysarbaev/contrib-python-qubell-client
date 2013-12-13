Writing tests
=============

We use python's unittests to create tests.
We have base class, where basic initialization made.

To add test, find existing test class that fits use-case or create new.


Hello-world test::

import qubell.api.tests.base as base


class FirstTest(base.BaseTestCasePrivate):

    def test_instance_launch(self):
        app = self.organization.application(manifest=self.manifest)
        self.assertTrue(app.name)             # we can get False if error

        instance = app.launch()
        self.assertTrue(instance)             # Instance launch will return False if errors
        self.assertTrue(instance.ready())     # Wait until instance become running

        self.assertFalse(app.delete())        # Should get error if delete app while it has running instance.
        self.assertTrue(instance.destroy())   # Destroying instance
        self.assertTrue(instance.destroyed()) # Wait until it destroyed
        self.assertTrue(app.delete())         # Delete application


This test creates application, and launches instance. Waits until it 'Running', then cleans.


Previous test could be written in more convenient way, using setups and teardowns::

	import os
	import qubell.api.tests.base as base
	from qubell.api.private.manifest import Manifest
	from qubell.api.tests.base import attr


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
_______________

- Every testclass should create it's own application. Use prefix in name as shown in example
- Use setUp and setUpClass for environment preparations. Test should only contain tested operations
- Do not forget to clean after tests
- The place where you create something is a good place to delete it. (if we create instance in test, delete it in test, not in teardown)
- Always check that operation succedded. You can get lot of false positives otherwise.
- Report as much as you can. It will make searching for fails easy.

Working tests and examples could be found in 'tests' directory.

