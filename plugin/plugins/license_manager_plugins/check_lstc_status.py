#!/usr/bin/env python2.7
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

# Python Std Lib
import re
import backend.lstc
import backend.util
from nagios.errorlevels import NagiosCritical, NagiosOk, NagiosUnknown
from nagios.arguments import process_plugin_options

def run():
    """Execute the plugin"""
    # Plugin arguments
    options = process_plugin_options()
    
    # Get the output of license manager command, catching errors
    try:
        if options.debug:
            output = backend.util.test_from_file("../tests/lstc_status.txt")
        else:
            output = backend.lstc.status("%s" % options.license)
    except backend.lstc.LstcStatusError as e:
        raise NagiosCritical("%s (code: %s, license: '%s') !" % (e.errmsg, e.retcode, e.license))

    # Globals
    connected_users = []

    for line in output:
        # Checking number of connected users
        connected_users_pattern = re.compile(r'^(?:\s+|)(\w+)\s+(\d+@[\w\d.]+)')
        connected_users_match = connected_users_pattern.search(line)
        if connected_users_match:
            connected_users.append((connected_users_match.group(1), connected_users_match.group(2)))

    # Checking for unknown errors
    if not connected_users:
        raise NagiosUnknown("Unexpected error ! Check with debug mode.")

    # Format Nagios output
    # --------------------
    #
    nagios_output = "LSTC: There %s %d license%s used."
    nagios_longoutput = ''

    # Plural syntax if more than 1 user
    if len(connected_users) > 1:
        verb = 'are'
        plural = 's'
    else:
        verb = 'is'
        plural =''

    # Output to Nagios
    nagios_output = nagios_output % (verb, len(connected_users), plural)
    if not options.nolongoutput:
        nagios_longoutput = '\n'
        for user in connected_users:
            nagios_longoutput += "User %s from host %s.\n" % (user[0], user[1])
    raise NagiosOk(nagios_output + nagios_longoutput)

# Main
if __name__ == "__main__":
    run()