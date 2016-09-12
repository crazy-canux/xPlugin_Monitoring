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

import pdm
from pdm.plugin import PDMLogin
from pdm.exceptions import PDMHttpError, PDMLoginFailed


plugin = PDMLogin("Test login to PDM using HTTP on a specified node.",
                  version=pdm.VERSION)

# Main tests
try:
    plugin.login()
    jsessionid = plugin.session.cookies["JSESSIONID"].split(":")

    # jsessionid is the list composed of [token, bad_cloneid, good_cloneid]
    # It has 3 values instead of 2 when the cloneid specified from command line
    # cannot be reached.
    if len(jsessionid) > 2:
        print "CRITICAL - Login on node '{}' is not possible !".format(
            plugin.args.cloneid)
        raise SystemExit(2)
    else:
        print "OK - Login is successful on node '{}'.".format(
            plugin.args.cloneid)
        raise SystemExit(0)
except PDMLoginFailed as e:
    # Login has failed
    print "CRITICAL - %s" % e
    raise SystemExit(2)
except PDMHttpError as e:
    # Unexpected HTTP error
    print "CRITICAL - %s" % e
    raise SystemExit(2)
finally:
    plugin.logout()