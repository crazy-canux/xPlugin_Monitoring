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

class NagiosCritical(Exception):
    """Exception raised to fire a CRITICAL event to Nagios and break the plugin"""
    def __init__(self, msg):
        print "CRITICAL - %s" % msg
        raise SystemExit(2)

class NagiosWarning(Exception):
    """Exception raised to fire a WARNING event to Nagios and break the plugin"""
    def __init__(self, msg):
        print "WARNING - %s" % msg
        raise SystemExit(1)

class NagiosUnknown(Exception):
    """Exception raised to fire a UNKNOWN event to Nagios and break the plugin"""
    def __init__(self, msg):
        print "UNKNOWN - %s" % msg
        raise SystemExit(3)

class NagiosOk(Exception):
    """Exception raised to fire a OK event to Nagios and break the plugin"""
    def __init__(self, msg):
        print "OK - %s" % msg
        raise SystemExit(0)