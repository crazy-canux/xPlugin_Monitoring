#!/usr/bin/env python
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
Plugin check_lbl_haproxy_connection.py.

Checks current connections.
"""

__version__ = "git"

import logging
from monitoring.nagios.plugin import NagiosPluginSSH
import requests

logger = logging.getLogger('plugin.unix')

# define new args
class PluginCFile(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginCFile,self).define_plugin_arguments()
        self.required_args.add_argument('-l','--login',
                                           dest="login",
                                           help="login to connect on the page, a string.",
                                           required=False)
        self.required_args.add_argument('-w','--password_web',
                                           dest="password_web",
                                           help="password to connect on the page, a string.",
                                           required=False)
        self.required_args.add_argument('-f', '--fileapp',
                                        dest="file_app",
                                        help="File of application, an string",
                                        required=False)

# Init plugin
plugin = PluginCFile(version=__version__, description="Check Currents Connections")

# checkout file
if plugin.options.file_app:
    cmd_file = "cat {0}".format(plugin.options.file_app)
    logger.debug("cmd_file : {0}".format(cmd_file))

    command_file = plugin.ssh.execute(cmd_file)
    output_file = command_file.output
    errors_file = command_file.errors
    logger.debug("output_file : {0}".format(output_file))

    if errors_file:
        plugin.unknown("Errors found:\n{}".format("\n".join(errors_file)))
else:
   output_file = None


r = requests.get("http://"+ plugin.options.hostname +":7777/;csv", auth=(plugin.options.login, plugin.options.password_web))

if r.status_code == 404 or r.status_code == 500:
    "Didn't checkout the csv: error HTTP: " + r.status_code

status = plugin.warning
plugin.shortoutput = "Haven't connections!"


data=[]
data_temp =  r.content.split('\n')
for d in data_temp:
    data.append(d.split(','))

logger.debug(data[0])

del data[0]
del data[len(data)-1]

for serv in output_file:
    for h in data:
        if len(h)>2 and h[0]!='stats' and h[0]==serv:
            logger.debug(h[0] +" " +h[1]+"_in " +h[8])
            logger.debug(h[0] +" " +h[1]+"_out " +h[9])
            status = plugin.ok
            plugin.perfdata.append('{table}={value};;;0'.format(table=h[0] + "_" + h[1] + "_in" , value= h[8]))
            plugin.longoutput.append('{table} : {value}'.format(table=h[0] + " -> " + h[1] + "_in" , value= h[8]))
            plugin.perfdata.append('{table}={value};;;0'.format(table=h[0] + "_" + h[1] + "_out" , value= h[9]))
            plugin.longoutput.append('{table} : {value}'.format(table=h[0] + " -> " + h[1] + "_out" , value= h[9]))
            plugin.shortoutput = "Have connections!"

status(plugin.output(long_output_limit=None))
