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
__version__ = "1.0.1"
__email__ = "vkhomenko@qubell.com"

from time import sleep

from qubellclient.tests import base
from qubellclient.private.manifest import Manifest
from qubellclient.tests.base import attr
from qubellclient.tools import rand
import os

prefix = rand()

class HierarchicalAppTest(base.BaseTestCasePrivate):


    @classmethod
    def setUpClass(cls):
        super(HierarchicalAppTest, cls).setUpClass()

    # Create applications for tests
        cls.parent = cls.organization.application(name="%s-test-hierapp-parent" % prefix, manifest=cls.manifest)
        cls.child_one = cls.organization.application(name="%s-test-hierapp-child-one" % prefix, manifest=cls.manifest)
        cls.child_two = cls.organization.application(name="%s-test-hierapp-child-two" % prefix, manifest=cls.manifest)
        cls.child_three = cls.organization.application(name="%s-test-hierapp-child-tree" % prefix, manifest=cls.manifest)

    # Create shared instance ONE to use in tests
        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), 'child.yml'))
        mnf.patch('application/components/child_app/configuration/configuration.workflows/launch/return/own/value', 'Child1 Ahoy!')
        cls.child_one.upload(mnf)
        cls.child_one_instance = cls.child_one.launch(destroyInterval=600000)
        assert cls.child_one_instance.ready()
        cls.child_one_revision = cls.child_one.revisionCreate(name='%s-tests-basic-hierapp-shared-one' % prefix, instance=cls.child_one_instance)


    # Create shared instance Two to use in tests
        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), 'child.yml'))
        mnf.patch('application/components/child_app/configuration/configuration.workflows/launch/return/own/value', 'Child2 Welcomes you')
        cls.child_two.upload(mnf)
        cls.child_two_instance = cls.child_two.launch(destroyInterval=600000)
        assert cls.child_two_instance.ready()
        cls.child_two_revision = cls.child_two.revisionCreate(name='%s-tests-basic-hierapp-shared-two' % prefix, instance=cls.child_two_instance)



        params = ''.join('%s: %s\n' % (cls.child_one_revision.revisionId.split('-')[0], cls.child_one_instance.instanceId))
        params += ''.join('%s: %s' % (cls.child_two_revision.revisionId.split('-')[0], cls.child_two_instance.instanceId))

        cls.shared_service = cls.organization.service(name='%s-HierarchicalAppTest-instance' % prefix,
                                                          type='builtin:shared_instances_catalog',
                                                          parameters=params)
        cls.environment.serviceAdd(cls.shared_service)


    # Create non shared instance Three to use in tests
        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), 'child.yml'))
        mnf.patch('application/components/child_app/configuration/configuration.workflows/launch/return/own/value', 'Child3 raises hands')
        cls.child_three.upload(mnf)
        cls.child_three_instance = cls.child_three.launch(destroyInterval=600000)


    @classmethod
    def tearDownClass(cls):
        super(HierarchicalAppTest, cls).tearDownClass()

    # Remove created services
        cls.environment.serviceRemove(cls.shared_service)
        cls.shared_service.delete()

    # Clean apps
        cls.parent.clean()
        cls.child_one.clean()
        cls.child_two.clean()
        cls.child_three.clean()

        cls.parent.delete()
        cls.child_one.delete()
        cls.child_two.delete()
        cls.child_three.delete()


    @attr('smoke')
    def test_launch_basic_non_shared_hierapp(self):
        """ Launch hierarchical app with child as not shared instance. Check that launching parent launches child instance.
        """
        pmnf = Manifest(file=os.path.join(os.path.dirname(__file__), "parent_child1.yml")) #Todo: resolve paths
        pmnf.patch('application/components/child/configuration/__locator.application-id', self.child_three.applicationId)
        self.parent.upload(pmnf)
        parent_instance = self.parent.launch(destroyInterval=300000)
        self.assertTrue(parent_instance.ready(), "Instance failed to start")

        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')
        self.assertNotEqual(parent_instance.submodules[0]['id'], self.child_three_instance.instanceId)
        self.assertTrue(parent_instance.destroy())


    def test_launch_hierapp_shared_instance(self):
        """ Launch hierarchical app with shared instance.
        """

        pmnf = Manifest(file=os.path.join(os.path.dirname(__file__), "parent_child1.yml")) #Todo: resolve paths
        pmnf.patch('application/components/child/configuration/__locator.application-id', self.child_one.applicationId)

        parameters = {self.child_one.name: {'revisionId': self.child_one_revision.revisionId}}

        # Api BUG?? TODO
        parameters = {
                "parent_in.child_input": "Hello from parent to child",
                "child": {
                    "revisionId": self.child_one_revision.revisionId
            }}


        self.parent.upload(pmnf)
        parent_instance = self.parent.launch(destroyInterval=600000, parameters=parameters)
        self.assertTrue(parent_instance.ready(), "Parent instance failed to start")

        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')
        self.assertEqual(parent_instance.submodules[0]['id'], self.child_one_instance.instanceId)

        # Shouldn't be able to remove child while parent use it and should return error
        # TODO: BUG
        #self.assertFalse(child_instance.destroy())

        self.assertTrue(parent_instance.destroy())



    @attr('smoke')
    def test_launch_hierapp_with_combined_child_instances(self):
        """ Launch hierarchical app with two shared and one non shared instance.
        """

        pmnf = Manifest(file=os.path.join(os.path.dirname(__file__), "parent_childs.yml")) #Todo: resolve paths
        pmnf.patch('application/components/child-one/configuration/__locator.application-id', self.child_one.applicationId)
        pmnf.patch('application/components/child-two/configuration/__locator.application-id', self.child_two.applicationId)
        pmnf.patch('application/components/child-three/configuration/__locator.application-id', self.child_three.applicationId)

        # TODO: bug. Need to pass params
        parameters = {
                "parent_in.child_three_input": "Hello from parent to child3 BUG",
                "child-one": {
                    "revisionId": self.child_one_revision.revisionId},
                "child-two": {
                    "revisionId": self.child_two_revision.revisionId}}


        self.parent.upload(pmnf)
        parent_instance = self.parent.launch(destroyInterval=600000, parameters=parameters)
        self.assertTrue(parent_instance.ready(), "Parent instance failed to start")

        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')
        sub = parent_instance.submodules

        self.assertTrue(len([sid for sid in sub if sid['id'] == self.child_one_instance.instanceId]))  # Way i search for id
        self.assertTrue(len([sid for sid in sub if sid['id'] == self.child_two_instance.instanceId]))
        self.assertFalse(len([sid for sid in sub if sid['id'] == self.child_three_instance.instanceId]))


        # Shouldn't be able to remove child while parent use it and should return error
        # TODO: BUG
        #self.assertFalse(child_instance.destroy())

        self.assertTrue(parent_instance.destroy())
