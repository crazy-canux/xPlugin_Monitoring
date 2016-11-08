# -*- coding: utf-8 -*-
# Copyright (C) Canux <http://www.Company.com/>
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

from datetime import datetime

import powershell

from powershell.xml.exceptions import XMLValidityError


class PowershellXMLTestCase(unittest.TestCase):
    def test_no_valid_xml_root_tag(self):
        """Test when the XML has no valid root tag."""
        with self.assertRaises(XMLValidityError):
            powershell.XMLTable("<xml><title>gdsg</title></xml>")

    def test_missing_xml_metadata(self):
        """Test when XML has no metadata (version, schema, ...)."""
        with self.assertRaises(XMLValidityError):
            powershell.XMLTable("<objs><title>gdsg</title></objs>")

    def test_not_supported_xml_version(self):
        """Test when the XML version is not supported."""
        with self.assertRaises(XMLValidityError):
            powershell.XMLTable(
                "<objs version='2.0.4' xmlns='test'><s>123456789</s></objs>")

    def test_xml_timestamp(self):
        """Test that the XML timestamp can be parsed to a datetime object."""
        xml = powershell.XMLTable(open(os.path.join(TESTS_DIR, 'sample.xml')))
        self.assertIsInstance(xml.last_modified, datetime)

    def test_xml_has_no_tabular_data(self):
        """Test when XML has no tabular data."""
        with self.assertRaisesRegexp(XMLValidityError, r'^No tabular data.*'):
            powershell.XMLTable(open(os.path.join(TESTS_DIR,
                                                  'sample_dag.xml')))

    def test_xml_has_no_serialized_object(self):
        """Test when the XML has no serialized object."""
        with self.assertRaisesRegexp(XMLValidityError,
                                     r'^No serialized object.*'):
            powershell.XMLSerializedTable(open(os.path.join(TESTS_DIR,
                                                            'sample.xml')))