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

import logging
import traceback
from pprint import pformat
from monitoring.nagios.plugin import NagiosPluginMSSQL

logger = logging.getLogger('plugin.sql')

# define new args
class PluginMSSQL(NagiosPluginMSSQL):
    def define_plugin_arguments(self):
        super(PluginMSSQL,self).define_plugin_arguments()

        self.required_args.add_argument('-s', '--accountsearch',
                                        dest="account_search",
                                        help="Acount Search, an string",
                                        required=True)

# Init plugin
plugin = PluginMSSQL(version="1.0",
                    description="check Account SQL" )
plugin.shortoutput = "Account SQL {0} exists".format(plugin.options.account_search)


# Final status exit for the plugin
status = None

# SQL query

result = plugin.query("select is_disabled from sys.server_principals where name = '{}'".format(plugin.options.account_search))

logger.debug(result)

if not result:
    status = plugin.critical
    plugin.shortoutput = "Account SQL {0} no exists".format(plugin.options.account_search)
else:
    if result[0]['is_disabled']:
        status = plugin.critical
        plugin.shortoutput = "Account SQL {0} is disabled".format(plugin.options.account_search)
    else:
        status = plugin.ok


# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
   status(plugin.output())
else:
   plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
