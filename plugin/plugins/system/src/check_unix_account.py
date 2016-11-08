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

__version__ = "git"

import logging
from monitoring.nagios.plugin import NagiosPluginSSH

logger = logging.getLogger('plugin.unix')

# define new args 
class PluginHadr(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginHadr,self).define_plugin_arguments()

        self.required_args.add_argument('-a', '--account',
                                        dest="account",
                                        help="account to check, an string",
                                        required=True)

# Init plugin
plugin = PluginHadr(version=__version__,
                    description="Check Unix Account")


# Final status exit for the plugin
status = None


cmd="id {0}".format(plugin.options.account)
logger.debug("cmd : {0}".format(cmd))

command = plugin.ssh.execute(cmd)
output = command.output
errors = command.errors

if command.status > 0:
    status = plugin.critical
    plugin.shortoutput = "Account {0} does not exist !".format(plugin.options.account)
    plugin.longoutput.append("\n".join(errors))

# Travel output cmd by line
cmpt = 0
for line in output:
    logger.debug("result : {}".format(line))

    status = plugin.ok
    plugin.shortoutput = "Account {0} exists".format(plugin.options.account)
    plugin.longoutput.append(line)
    

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
   status(plugin.output())
else:
   plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
