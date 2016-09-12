#!/usr/bin/env python2.7
#-*- coding: UTF-8 -*-
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

"""
Plugin check_snmp_uptime.py.

Checks current connections.
"""

__version__ = "git"

import logging
from monitoring.nagios.plugin import NagiosPlugin
import requests
import os
import commands
from datetime import datetime
import time

logger = logging.getLogger('plugin.unix')

# define new args
class PluginGet_Uptime(NagiosPlugin):
    def define_plugin_arguments(self):
        super(PluginGet_Uptime,self).define_plugin_arguments()
        self.required_args.add_argument('-C','--community',
                                        dest="community",
                                        help="community to connect on switch , a string.",
                                        required=True)
        self.required_args.add_argument('-w',
                                        dest="warning",
                                        type=int,
                                        help="This is our warning threshold, "
                                        "an integer.",
                                        default=0,
                                        required=False)
        self.required_args.add_argument('-c',
                                        dest="critical",
                                        type=int,
                                        help="This is our critical threshold, "
                                        "an integer.",
                                        default=0,
                                        required=False)
# Init plugin
plugin = PluginGet_Uptime(version=__version__, description="Check Uptime Switch")


cmd_get_uptime = "snmpget -t 1 -r 5 -m '' -v 2c -c {0} {1}:161 .1.3.6.1.4.1.1872.2.5.1.3.1.12.0 ".format(plugin.options.community,plugin.options.hostname)
logger.debug("cmd_get_uptime : {0}".format(cmd_get_uptime))

status, output = commands.getstatusoutput(cmd_get_uptime)
date = output.split('STRING: "')[1].split(' (')[0]
date_object = datetime.strptime(date,"%H:%M:%S %a %b %d, %Y")

logger.debug("date_object : {0}".format(date_object))

date_now = datetime.now()
diff  = date_now - date_object
logger.debug("nb of days: {0}".format(diff.days))
if (diff.days >= plugin.options.warning):
    status = plugin.ok
else:
    status = plugin.warning
plugin.shortoutput = "nb of days: " + str(diff.days)
plugin.longoutput.append("nb of days: " + str(diff.days) + " -> " + output)

status(plugin.output(long_output_limit=None))
