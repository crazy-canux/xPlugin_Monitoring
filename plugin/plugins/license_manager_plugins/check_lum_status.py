#!/usr/bin/env python2.7
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

# Python Std Lib
import re
import backend.lum
import backend.util
from nagios.errorlevels import NagiosCritical, NagiosOk
from nagios.arguments import process_plugin_options

def run():
    """Execute the plugin"""
    # Plugin arguments
    options = process_plugin_options()
    
    # Get the output of license manager command, catching errors
    try:
        if options.debug:
            output = backend.util.test_from_file("../tests/lum_status.txt")
        else:
            output = backend.lum.status("{0.license}".format(options))
    except backend.lum.LumStatusError as e:
        raise NagiosCritical("{0.errmsg} (code: {0.retcode}, license: '{0.license}') !".format(e))

    # Find line showing state of license server
    servers_up = []
    for line in output:
        server_state_line_pattern = re.compile(r"\s+ip:(.*)\s\(WIN32\)")
        server_state_line_match = server_state_line_pattern.search(line)
        if server_state_line_match:
            servers_up.append(server_state_line_match.group(1))

    # Format output to Nagios
    nagios_longoutput = ""
    nagios_output = ""
    if len(servers_up) > 0:
        if not options.nolongoutput:
            for server in servers_up:
                nagios_longoutput += "\nServer up: {0}".format(server)

        if len(servers_up) > 1:
            nagios_output = "{0} servers are serving licenses.".format(len(servers_up))
        else:
            nagios_output = "{0} server is serving license.".format(len(servers_up))
        raise NagiosOk(nagios_output + nagios_longoutput)
    else:
        raise NagiosCritical("LUM status is not correct, please check !")

# Main
if __name__ == "__main__":
    run()