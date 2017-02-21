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

"""Check that HADR is available."""

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
                                        help='Warning threshold for log_gap.',
                                        required=False)

        self.required_args.add_argument('-c', '--crit',
                                        type=int,
                                        dest='critical',
                                        default=0,
                                        help='Critical threshold for log_gap.',
                                        required=False)

# Init plugin
plugin = PluginHadr(version=hadr.__version__,
                    description="check HADR statut")
plugin.shortoutput = "HADR is Connected"


# Final status exit for the plugin
status = None

cmd = """echo 'db2 \"SELECT HADR_ROLE, \
HADR_LOCAL_HOST, \
HADR_CONNECT_STATUS, \
HADR_REMOTE_HOST, \
HADR_LOG_GAP, \
HADR_STATE \
FROM SYSIBMADM.SNAPHADR\"' \
| sudo -u {0} -i \
| sed -n '/--/{{n; p;}}' \
| sed 's/[ ][ ]*/ /g'""".format(plugin.options.db2_user)

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

if not any(output):
    plugin.unknown("Output is empty !")

for line in output:
    logger.debug(line)

    status = plugin.ok
    role, name, state, remote, log_gap, hadr_state = line.split()

    plugin.longoutput.append("Active Host: {0}  "
                             "Role: {1}{2}"
                             "Remote Host: {3}{2}"
                             "State: {4}{2}"
                             "Log_Gap: {5}{2}"
                             "HADR_State: {6}".format(name,
                                                      role,
                                                      '\n',
                                                      remote,
                                                      state,
                                                      log_gap,
                                                      hadr_state))

    plugin.perfdata.append(
        'log_gap[{0}]={1}b;{2.warning};{2.critical};0;'.format(cmpt,
                                                               log_gap,
                                                               plugin.options))
    cmpt += 1

    if state != "CONNECTED":
        plugin.shortoutput = "HADR is {}".format(state)
        plugin.critical(plugin.output())

    if hadr_state != "PEER":
        plugin.shortoutput = "Hadr state is {}".format(hadr_state)
        plugin.warning(plugin.output())

    # Log_gap
    if plugin.options.warning:
        if int(log_gap) >= plugin.options.warning:
            status = plugin.warning
            plugin.shortoutput = "Log_gap : {}   " \
                                 "(threshold warn {})".format(
                                     log_gap, plugin.options.warning)
    if plugin.options.critical:
        if int(log_gap) >= plugin.options.critical:
            status = plugin.critical
            plugin.shortoutput = "Log_gap : {}   " \
                                 "(threshold crit {})".format(
                                     log_gap, plugin.options.critical)

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
