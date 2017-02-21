#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#===============================================================================
# Copyright (c) Canux CHENG <canuxcheng@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#===============================================================================

"""
Perform Unit tests.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from generic.parser import BaseParser
from generic.parser.exceptions import RawValueNameError

from generic.parser.json import JSONParser
from generic.parser.json.exceptions import InvalidJSONData


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = BaseParser()
        self.parser.longoutput = ["foo", "bar", "baz"]
        self.parser._raw_value = {"foo": 1, "bar": 2, "baz": 3}

    def test_base_parser_longoutput(self):
        self.assertEqual("foo\nbar\nbaz", self.parser.print_longoutput)

    def test_base_parser_iterable(self):
        for value in self.parser:
            self.assertIsInstance(value, tuple)

    def test_base_parser_get_value(self):
        self.assertEqual(self.parser["bar"], 2)

    def test_base_parser_value_not_found(self):
        with self.assertRaisesRegexp(RawValueNameError, "No raw value"):
            print self.parser["toto"]

    def test_base_parser_keys(self):
        self.assertListEqual(["bar", "baz", "foo"],
                             sorted(self.parser.value_keys))


class JSONParserTest(unittest.TestCase):
    def setUp(self):
        self.json_data = r'{ "longoutput": ["The appcmd list request has no ' \
                         r'requests in the queue."],' \
                         r'"raw_value": { "request_queue": 0 } }'
        self.json_invalid_longoutput = r'{ "longoutput": "toto",' \
                                       r'"raw_value": { "request_queue": 0 } }'
        self.json_invalid_raw_value = r'{ "longoutput": ["tata"],' \
                                      r'"raw_value": "hello" }'
        self.json_invalid_data = "{fdds}"

    def test_json_parser_invalid_data(self):
        with self.assertRaises(InvalidJSONData):
            json_parser = JSONParser(self.json_invalid_data)

    def test_json_parser_get_value(self):
        json_parser = JSONParser(self.json_data)
        self.assertEqual(0, json_parser["request_queue"])

    def test_json_parser_longoutput_invalid_type(self):
        with self.assertRaises(TypeError):
            json_parser = JSONParser(self.json_invalid_longoutput)

    def test_json_parser_raw_value_invalid_type(self):
        with self.assertRaises(TypeError):
            json_parser = JSONParser(self.json_invalid_raw_value)

if __name__ == '__main__':
    print "Performing tests...\n".upper()
    unittest.main(verbosity=2)