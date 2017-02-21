# -*- coding: utf-8 -*-
# Copyright (C) Canux CHENG <canuxcheng@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Test the powershell XML parsing."""

import unittest
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

import sys
sys.path.insert(0, os.path.join(TESTS_DIR, '../src'))

import powershell


class PowershellSerializationTestCase(unittest.TestCase):
    def setUp(self):
        self.objs = powershell.XMLSerializedTable(
            open(os.path.join(TESTS_DIR, 'sample_dag.xml')))

    def test_object_has_property(self):
        """Test that the serialized object has property Identity."""
        self.assertTrue(self.objs[0].has_property('Identity'))

    def test_object_has_property_value(self):
        """Test that the object's Indentity property is not null."""
        self.assertIsNotNone(self.objs[0]['Identity'])

    def test_match_property_value(self):
        """Test that the property Status is either Healthy or Mounted."""
        self.assertIsNotNone(self.objs.match('Status',
                                             r'(Healthy|Mounted)'))

    def test_match_databasecopystatusentry_property_value(self):
        """Test that a Database's Status is Healthy or Mounted."""
        self.assertIsNotNone(
            self.objs.match('Status',
                            r'(Healthy|Mounted)',
                            object_name='DatabaseCopyStatusEntry'))

    def test_match_replicationcheckoutcome_property_value(self):
        """Test that a Replication's Result has Passed."""
        self.assertIsNotNone(
            self.objs.match('Result',
                            r'Passed',
                            object_name='ReplicationCheckOutcome'))

    def test_match_replicationcheckoutcome_result_failed(self):
        """Test for Replication's Result failed."""
        match = self.objs.match('Result',
                                r'^Passed$',
                                object_name='ReplicationCheckOutcome',
                                invert=True)
        self.assertEqual(match[0]['Result'], 'Error')

    def test_object_names(self):
        """Test that object names are unique."""
        self.assertEqual(self.objs.list_object_names(),
                         {u'ReplicationCheckOutcome',
                          u'DatabaseCopyStatusEntry'})

    def test_property_value_is_integer(self):
        """Test "i32/i64" property conversion to int."""
        self.assertIsInstance(self.objs.get(1)['SinglePageRestore'], int)

    def test_property_value_is_unicode(self):
        """Test "s" property conversion to unicode."""
        self.assertIsInstance(self.objs.get(1)['DatabaseName'], unicode)

    def test_property_value_is_boolean(self):
        """Test "b" property conversion to bool."""
        self.assertIsInstance(self.objs.get(1)['ActivationSuspended'], bool)