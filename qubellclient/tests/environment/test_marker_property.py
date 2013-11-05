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

from qubellclient.tests import base
from qubellclient.private.manifest import Manifest
import os


class MarkerPropertyTest(base.BaseTestCasePrivate):

    @classmethod
    def setUpClass(cls):
        super(MarkerPropertyTest, cls).setUpClass()

    # Create applications for tests
        cls.app = cls.organization.application(name="%s-test-marker-property" % cls.prefix, manifest=cls.manifest)

    @classmethod
    def tearDownClass(cls):
        super(MarkerPropertyTest, cls).tearDownClass()

    # Clean apps
        cls.app.clean()
        cls.app.delete()


    def test_marker_crud(self):
        self.assertTrue(self.environment.markerAdd('TEST-MARKER'))
        mrk = [p for p in self.environment.json()['markers'] if p['name'] == 'TEST-MARKER']
        self.assertTrue(len(mrk))
        self.assertEqual(mrk[0]['name'], 'TEST-MARKER')
        self.assertTrue(self.environment.markerRemove('TEST-MARKER'))

        mrk = [p for p in self.environment.json()['markers'] if p['name'] == 'TEST-MARKER']
        self.assertFalse(len(mrk))

    def test_property_crud(self):
        self.assertTrue(self.environment.propertyAdd(name='test-name', type='string', value='TEST-PROPERTY'))
        prop = [p for p in self.environment.json()['properties'] if p['name'] == 'test-name']
        self.assertTrue(len(prop))
        self.assertEqual(prop[0]['name'], 'test-name')
        self.assertEqual(prop[0]['value'], 'TEST-PROPERTY')
        self.assertTrue(self.environment.propertyRemove('test-name'))
        prop = [p for p in self.environment.json()['properties'] if p['name'] == 'test-name']
        self.assertFalse(len(prop))

    def test_marker_property_usage(self):
        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), "marker-property.yml")) #Todo: resolve paths
        self.app.upload(mnf)
        self.assertTrue(self.environment.propertyAdd(name='sample-property-str', type='string', value='test-property-string'))
        self.assertTrue(self.environment.propertyAdd(name='sample-property-int', type='int', value='42'))
        self.assertTrue(self.environment.propertyAdd(name='sample-property-obj', type='object', value='aa:bb'))
        self.assertTrue(self.environment.markerAdd('test-marker'))

        ins = self.app.launch(destroyInterval=300000)
        self.assertTrue(ins.ready(), 'Instance failed to start') # This manifest require marker. Will get error if no marker present

        out = ins.returnValues
        self.assertEqual(out['output.str'], 'test-property-string')
        self.assertEqual(out['output.int'], '42')
        self.assertEqual(out['output.obj'], 'aa:bb')

        # TODO: instance should be destroyed before properties removed, otherwise it will be in inconsistent state and
        self.app.clean()

        self.assertTrue(self.environment.propertyRemove(name='sample-property-str'))
        self.assertTrue(self.environment.propertyRemove(name='sample-property-int'))
        self.assertTrue(self.environment.propertyRemove(name='sample-property-obj'))
        self.assertTrue(self.environment.markerRemove('test-marker'))

