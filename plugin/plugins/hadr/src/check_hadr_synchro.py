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

"""Check that HADR is in sync."""

import logging
from monitoring.nagios.plugin import NagiosPluginSSH
import hadr

logger = logging.getLogger('plugin.hadr')


# define new args
class PluginHadr(NagiosPluginSSH):
    """Custom plugin definition."""
    def define_plugin_arguments(self):
        super(PluginHadr, self).define_plugin_arguments()

        self.required_args.add_argument('-d', '--db2user',
                                        dest="db2_user",
                                        help="Db2 user use, an string",
                                        required=True)

        self.required_args.add_argument('-w', '--warn',
                                        type=int,
                                        dest='warning',
                                        default=0,
                                        help='Warning threshold.',
                                        required=False)

        self.required_args.add_argument('-c', '--crit',
                                        type=int,
                                        dest='critical',
                                        default=0,
                                        help='Critical threshold.',
                                        required=False)

# Init plugin
plugin = PluginHadr(version=hadr.__version__,
                    description="check HADR synchro")
plugin.shortoutput = "HADR is Synchro"


# Final status exit for the plugin
status = None


cmd = """echo 'db2 \"SELECT cast(substr(HADR_PRIMARY_LOG_FILE,2,7) as INT) - \
cast(substr(HADR_STANDBY_LOG_FILE,2,7) as INT) as \
DIFF_LOG_BETWEEN_STDY_AND_PRIM \
FROM SYSIBMADM.SNAPHADR\"' \
| sudo -u {0} -i \
| sed -n '/--/{{n; p;}}' \
| sed 's/[ ][ ]*//g'""".format(plugin.options.db2_user)

logger.debug("cmd : {0}".format(cmd))

try:
    command = plugin.ssh.execute(cmd)
except plugin.ssh.SSHCommandTimeout:
    plugin.unknown("Plugin execution timed out in {} secs !".format(
        plugin.options.timeout))

output = command.output
errors = command.errors

if errors:
    plugin.unknown("Errors found:\n{}".format("\n".join(errors)))

# Travel output cmd by line
cmpt = 0
for line in output:
    logger.debug(line)

    status = plugin.ok
    diff_log = line.strip()

    logger.debug("diff_log : {}".format(diff_log))

    plugin.perfdata.append(
        'log_diff[{0}]={1}c;{2.warning};{2.critical};0;'.format(
            cmpt, diff_log, plugin.options))
    cmpt += 1

    # Check threshold
    if plugin.options.warning:
        if int(diff_log) >= plugin.options.warning:
            status = plugin.warning
            plugin.shortoutput = "DIFF LOG BETWEEN STDY AND PRIM : {}   " \
                                 "(threshold warn {})".format(
                                     diff_log, plugin.options.warning)
    if plugin.options.critical:
        if int(diff_log) >= plugin.options.critical:
            status = plugin.critical
            plugin.shortoutput = "DIFF LOG BETWEEN STDY AND PRIM : {}   " \
                                 "(threshold crit {})".format(
                                     diff_log, plugin.options.critical)

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, '
                   'please investigate with debug mode on.')
