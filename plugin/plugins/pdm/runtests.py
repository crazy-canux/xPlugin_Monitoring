#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#===============================================================================
# Copyright (c) 2013 Faurecia, Monitoring & Reporting
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
Unit tests for this project.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import unittest

from pdm.plugin import PDMLogin
from pdm.exceptions import PDMLoginFailed, PDMHttpError


class PDMLoginTest(unittest.TestCase):
    def test_get_jsession_token(self):
        plugin = PDMLogin(
            arguments=["--url", "http://numgen.app.corp:11105/prod_ng",
                       "--cloneid", "17cu31omc",
                       "--login", "csu",
                       "--password", "P@ssw0rd"])
        token = plugin.jsession_token
        self.assertRegexpMatches(token, r"^0{4}")

    def test_set_jsession_cookie(self):
        plugin = PDMLogin(
            arguments=["--url", "http://numgen.app.corp:11105/prod_ng",
                       "--cloneid", "17cu31omc",
                       "--login", "csu",
                       "--password", "P@ssw0rd"])
        cookie = plugin._create_jsession_cookie()
        self.assertIn("JSESSIONID", cookie)

    def test_good_cloneid(self):
        plugin = PDMLogin(
            arguments=["--url", "http://numgen.app.corp:11105/prod_ng",
                       "--cloneid", "17cu31omd",
                       "--login", "csu",
                       "--password", "P@ssw0rd"])
        plugin.login()
        cloneid = plugin.session.cookies["JSESSIONID"].split(":")[1]
        self.assertEqual("17cu31omd", cloneid)

    def test_bad_cloneid(self):
        plugin = PDMLogin(
            arguments=["--url", "http://numgen.app.corp:11105/prod_ng",
                       "--cloneid", "17cu31oma",
                       "--login", "csu",
                       "--password", "P@ssw0rd"])
        plugin.login()
        cloneids = plugin.session.cookies["JSESSIONID"].split(":")[1:]
        self.assertEqual(2, len(cloneids))

    def test_unauthorized_login(self):
        plugin = PDMLogin(
            arguments=["--url", "http://numgen.app.corp:11105/prod_ng",
                       "--cloneid", "17cu31oma",
                       "--login", "csua",
                       "--password", "P@ssw0rd"])
        with self.assertRaises(PDMLoginFailed):
            plugin.login()

    def test_http_error(self):
        plugin = PDMLogin(
            arguments=["--url", "http://numgen.app.corp:11108/prod_ng",
                       "--cloneid", "17cu31oma",
                       "--login", "csu",
                       "--password", "P@ssw0rd"])
        with self.assertRaises(PDMHttpError):
            plugin.login()

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(PDMLoginTest)
    unittest.TextTestRunner(verbosity=2).run(suite)