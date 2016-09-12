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
Plugin check_lbl_haproxy_conn_state.py.

Checks connexion state on slave.
"""

__version__ = "git"

import logging
from monitoring.nagios.plugin import NagiosPlugin
import requests

logger = logging.getLogger('plugin.unix')

# define new args
class PluginCFile(NagiosPlugin):
    def define_plugin_arguments(self):
        super(PluginCFile,self).define_plugin_arguments()
        self.required_args.add_argument('-s', '--second',
                                        dest="host",
                                        help="address ip of second server , a string",
                                        required=True)
        self.required_args.add_argument('-l','--login',
                                           dest="login",
                                           help="login to connect on the page, a string.",
                                           required=False)
        self.required_args.add_argument('-p','--password',
                                           dest="password",
                                           help="password to connect on the page, a string.",
                                           required=False)
        self.required_args.add_argument('-c','--conn',
                                           dest="connexion",
		                    			   type=int,
                                           help="minimum connexion to define if slave became the master , an integer.",
                                           required=False)
        self.required_args.add_argument('-i','--invert',
                                           dest="invert",
                    					   action="store_true",
                                           help="Invert Status, WARNING becomes OK ",
                                           required=False)


# Init plugin
plugin = PluginCFile(version=__version__, description="Check Connexion State")

r = requests.get("http://"+ plugin.options.host +":7777/;csv", auth=(plugin.options.login, plugin.options.password))

if r.status_code == 404 or r.status_code == 500:
    "Didn't checkout the csv: error HTTP: " + r.status_code

data=[]
data_temp =  r.content.split('\n')
for d in data_temp:
    data.append(d.split(','))

if plugin.options.invert:
    status = plugin.warning
    plugin.shortoutput = "Master haven't got any connections"
else:
    status = plugin.ok
    plugin.shortoutput = "Slave haven't got any connections"
logger.debug(data[0])

del data[0]
del data[len(data)-1]
for h in data:
    if len(h)>2 and h[0]!='stats':
        logger.debug(h[0] +" " +h[1]+" " +h[4])
        if int(h[4]) > plugin.options.connexion:
	        if plugin.options.invert:
		    status = plugin.ok
	            plugin.shortoutput = "Master have got connections"
                    plugin.longoutput.append("Master have got some connections: " +h[0] +" "+h[1]+": "+h[4])
	        else:
           	    status = plugin.warning
	            plugin.shortoutput = "Slave have got some connections: " +h[0] +" "+h[1]+": "+h[4]
                    plugin.longoutput.append("Slave have got some connections: " +h[0] +" "+h[1]+": "+h[4])

if len(plugin.longoutput)==0:
    if plugin.options.invert:
       	plugin.longoutput.append("Master haven't got any connections")
    else:
   	plugin.longoutput.append("Slave haven't got any connections")

status(plugin.output(long_output_limit=None))
