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


import os
import qubellclient.tests.base as base
from qubellclient.private.manifest import Manifest
from qubellclient.tools import rand

__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__version__ = "1.0.1"
__email__ = "vkhomenko@qubell.com"

class Constants(base.BaseTestCasePrivate):

    @classmethod
    def setUpClass(cls):
        super(Constants, cls).setUpClass()
        cls.client = cls.organization.application(name="%s-constants-reconfiguration" % cls.prefix, manifest=cls.manifest)

    @classmethod
    def tearDownClass(cls):
        super(Constants, cls).tearDownClass()
        cls.client.clean()
        cls.client.delete()

    def reconf(self, base_manifest, target_manifest):
        rnd = rand()
        self.client.upload(base_manifest)
        inst1 = self.client.launch(destroyInterval=300000)
        self.assertTrue(inst1, "%s-%s: Instance failed to launch" % (self.prefix, self._testMethodName))
        self.assertTrue(inst1.ready(), "Instance not 'running' after timeout")

        self.client.upload(target_manifest)
        inst2 = self.client.launch(destroyInterval=300000)
        self.assertTrue(inst2, "%s-%s: Instance failed to launch" % (self.prefix, self._testMethodName))
        self.assertTrue(inst2.ready(), "Instance not 'running' after timeout")

        rev2 = self.client.revisionCreate(name='%s-rev2' % rnd, instance=inst2)

        inst1.reconfigure(revisionId=rev2.revisionId)
        return inst1
        rev2.delete()

    # May fail because "Unknown status"
    def test_parameter_added(self):
        """ Reconfigure app adding new parameter. It should be shown after reconfiguration.
        """
        src = Manifest(file=os.path.join(os.path.dirname(__file__), "constants-base.yml"))
        dst = Manifest(file=os.path.join(os.path.dirname(__file__), "constants-added_parameter.yml"))
        reconfigured_inst = self.reconf(src, dst)
        self.assertTrue(reconfigured_inst.ready())

        self.assertEqual("Hello old param", reconfigured_inst.returnValues['return.foo'])
        self.assertEqual("Hello NEW param", reconfigured_inst.returnValues['return.bar'])

    def test_parameter_removed(self):
        """ Reconfigure app removing parameter. Old returns should be removed after reconfiguration.
        """
        src = Manifest(file=os.path.join(os.path.dirname(__file__), "constants-added_parameter.yml"))
        dst = Manifest(file=os.path.join(os.path.dirname(__file__), "constants-base.yml"))
        reconfigured_inst = self.reconf(src, dst)
        self.assertTrue(reconfigured_inst.ready())

        self.assertEqual("Hello single param", reconfigured_inst.returnValues['return.foo'])
        self.assertFalse(reconfigured_inst.returnValues.has_key('return.bar'))

    def test_parameter_type_change(self):
        """ Reconfigure app changing parameter type.
        """
        src = Manifest(file=os.path.join(os.path.dirname(__file__), "constants-base.yml"))
        dst = Manifest(file=os.path.join(os.path.dirname(__file__), "constants-parameter_type_change.yml"))
        reconfigured_inst = self.reconf(src, dst)
        self.assertTrue(reconfigured_inst.ready())

        self.assertEqual("42", reconfigured_inst.returnValues['return.foo'])
