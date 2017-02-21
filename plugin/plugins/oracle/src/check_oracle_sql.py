#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canux CHENG <canuxcheng@gmail.com>
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

import oracle

logger = logging.getLogger('plugin.connection')


# define new args
class PluginConnection(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginConnection, self).define_plugin_arguments()

        self.required_args.add_argument('--oracle-home',
                                        dest="oracle_home",
                                        default='/opt/oracle/ora11',
                                        help="Oracle Home. "
                                             "Default value is "
                                             "\"/opt/oracle/ora11\".",
                                        required=False)

        self.required_args.add_argument('--oracle-sqlplus',
                                        dest="oracle_sqlplus",
                                        help="Absolute path for sqlplus.",
                                        required=False,
                                        default="/opt/oracle/ora11/bin/sqlplus"
                                        )

        self.required_args.add_argument('--oracle-user',
                                        dest="oracle_user",
                                        default='oracle',
                                        help="Oracle user. "
                                             "Default value is \"oracle\".",
                                        required=False)

        self.required_args.add_argument('--oracle-db-sid',
                                        dest="oracle_db_sid",
                                        help="Oracle db SID.",
                                        required=True)

        self.required_args.add_argument('--oracle-db-user',
                                        dest="oracle_db_user",
                                        default='nagios',
                                        help="Oracle user. "
                                             "Default value is \"nagios\".",
                                        required=False)

        self.required_args.add_argument('--oracle-db-password',
                                        dest="oracle_db_password",
                                        default='nagios',
                                        help="Oracle Password. "
                                        "Default value is \"nagios\".",
                                        required=False)

        self.required_args.add_argument('--select',
                                        dest="select",
                                        default="count(*)",
                                        help="The sql argument select.",
                                        required=False)

        self.required_args.add_argument('--table',
                                        dest="table",
                                        help="The sql argument from.",
                                        required=True)

        self.required_args.add_argument('--where',
                                        dest="where",
                                        help="The sql argument where.",
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
plugin = PluginConnection(version=oracle.VERSION,
                          description="Check sql result.")

# Final status exit for the plugin
status = None

cmd = """echo "echo \\"select {0} \
from {1} \
where {2};\\" \
|{3} {4}/{5}@{6}" \
|sudo ORACLE_HOME={7} -i -u {8} \
|sed -n '/--/{{n; p;}}'""".format(plugin.options.select,
                                  plugin.options.table,
                                  plugin.options.where,
                                  plugin.options.oracle_sqlplus,
                                  plugin.options.oracle_db_user,
                                  plugin.options.oracle_db_password,
                                  plugin.options.oracle_db_sid,
                                  plugin.options.oracle_home,
                                  plugin.options.oracle_user)

logger.debug("cmd : {0}".format(cmd))

try:
    command = plugin.ssh.execute(cmd)
    output = command.output.pop()
    errors = command.errors
    logger.debug("Received output: {}".format(output))
    logger.debug("Received errors: {}".format(errors))

    if errors:
        plugin.unknown("Errors found:\n{}".format("\n".join(errors)))

    result = int(output)
    logger.debug("Result: {}".format(result))
    status = plugin.ok

    # Check threshold
    if plugin.options.warning:
        if result >= plugin.options.warning:
            status = plugin.warning
    if plugin.options.critical:
        if result >= plugin.options.critical:
            status = plugin.critical

    plugin.shortoutput = "The result is {number}."
    plugin.perfdata.append("{table}={value};{warn};{crit};0;".format(
        crit=plugin.options.critical,
        warn=plugin.options.warning,
        value=result,
        table=plugin.options.table.lower()))

    status(plugin.output({"number": result}))

    logger.debug("Return status and exit to Nagios.")

except plugin.ssh.SSHError as ssh_error_msg:
    plugin.shortoutput = "SSH error: {}".format(ssh_error_msg)
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())

except Exception:
    plugin.shortoutput = "Something unexpected happened ! " \
                         "Please investigate..."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())
