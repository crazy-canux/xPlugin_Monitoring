#!/usr/bin/env python2.7
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

import logging
import traceback
from monitoring.nagios.plugin import NagiosPluginSSH
from monitoring.nagios.plugin import argument

logger = logging.getLogger('plugin.cashcom')

# define new args
class PluginCashCom(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginCashCom,self).define_plugin_arguments()

        self.required_args.add_argument('-d', '--oraclep',
                                        dest="oraclep",
                                        default="oraclep",
                                        help="oraclep user use, an string",
                                        required=False)

        self.required_args.add_argument('-w', '--warn',
                                        type=argument.hours,
                                        dest='warning',
                                        default=0,
                                        help='Warning threshold.',
                                        required=False)

        self.required_args.add_argument('-c', '--crit',
                                        type=int,
                                        dest='critical',
                                        default=600,
                                        help='Critical threshold.',
                                        required=False)


# Init plugin
plugin = PluginCashCom(version="1.1.0",
                       description="Check application status for CashCom. "
                                   "Query the application database to know if "
                                   "it is always alive."
                      )

try:
    cmd = """echo "echo \\"SELECT CASE WHEN ((sysdate - to_date('1970-01-01','YYYY-MM-DD'))* 3600*24)-(substr(valeur,3) * 0.001)-(round((((sysdate - to_date('1970-01-01','YYYY-MM-DD'))* 3600*24) -(substr(valeur,3) * 0.001))/3600)*3600) > {0} \
    THEN 'KO' \
    ELSE 'OK' \
    END as \\"ALERTE\\" \
    FROM ebc.paramgeneral \
    WHERE id = 'CASHCOMPING';\\" \
    |sqlplus ops/operations@EBC_PROD" \
    |sudo -u {1} -i \
    |sed -n '/--/{{n; p;}}'""".format(plugin.options.critical, plugin.options.oraclep)

    command = plugin.ssh.execute(cmd)
    output = command.output[0]
    errors = command.errors

    logger.debug("Received output: %s", output)
    logger.debug("Received errors: %s", errors)
except:
    plugin.shortoutput = "Something unexpected happened ! Please investigate..."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")

if errors:
    plugin.shortoutput = "Errors returned during command execution !"
    plugin.longoutput = errors
    plugin.unknown(plugin.output())
elif 'OK' in output:
    plugin.shortoutput = "Application is alive."
    plugin.ok(plugin.output())
elif 'KO' in output:
    plugin.shortoutput = "Application is not responding !"
    plugin.critical(plugin.output())
else:
    plugin.shortoutput = "Cannot determinate application status !"
    plugin.unknown(plugin.output())
