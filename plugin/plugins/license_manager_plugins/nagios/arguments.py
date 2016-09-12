# -*- coding: utf-8 -*-
# Copyright (C) Faurecia <http://www.faurecia.com/>
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

import optparse
from nagios.errorlevels import NagiosUnknown

# Argument parser object
argparser = optparse.OptionParser()


def process_plugin_options():
    """Process plugin arguments"""
    argparser.add_option('-l',
                         dest='license',
                         help='License file or remote host as '
                              '<port>@<remote_host>')
    argparser.add_option('-p',
                         dest='port',
                         help='License port (only for backend that does not '
                              'support remote host as <port>@<remote_host>)')
    argparser.add_option('-d', '--debug',
                         dest='debug',
                         action='store_true',
                         help='Enable debug mode')
    argparser.add_option('-t', '--timeout',
                         dest='timeout',
                         help='Set a timeout in seconds (default 60 secs)',
                         default="30")
    argparser.add_option('--no-long-output',
                         dest='nolongoutput',
                         action='store_true',
                         help='Disable Nagios long output (compatibility with '
                              'Nagios < 3.x)')
    argparser.add_option('-a', '--with-stat',
                         dest='with_stat',
                         action='store_true',
                         help='Compute license stats (lmstat -a).')
    opt = argparser.parse_args()[0]

    # Checking for options
    if not opt.license:
        raise NagiosUnknown(
            "Syntax error: missing license or remote host information !")
    if opt.debug:
        print "Debug mode is on."

    return opt
