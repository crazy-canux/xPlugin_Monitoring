#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (C) 2015 Faurecia <http://www.faurecia.com/>
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

logger = logging.getLogger('plugin.connection')


# define new args
class PluginConnection(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginConnection, self).define_plugin_arguments()

        self.required_args.add_argument(
            '--oracle-home',
            dest="oracle_home",
            default='/appliprod/home/oracle',
            help="Path of Oracle installation. "
                 "Default to \"/appliprod/home/oracle\".",
            required=False)

        self.required_args.add_argument(
            '--oracle-user',
            dest="oracle_user",
            default='oraclep',
            help="Oracle instance user. Default to \"oraclep\".",
            required=False)

        self.required_args.add_argument(
            '-S', '--oracle-sid',
            dest="oracle_sid",
            default='EBC_PROD',
            help="Oracle SID. Default to \"EBC_PROD\".",
            required=False)

        self.required_args.add_argument(
            '--oracle-db-user',
            dest="oracle_db_user",
            default='ops',
            help="Oracle database user. Default to \"ops\".",
            required=False)

        self.required_args.add_argument(
            '--oracle-db-password',
            dest="oracle_db_password",
            default='operations',
            help="Oracle database user password. Default to \"operations\".",
            required=False)

        self.required_args.add_argument(
            '-w',
            type=int,
            dest='warning',
            default=0,
            help='Warning threshold.',
            required=False)

        self.required_args.add_argument(
            '-c',
            type=int,
            dest='critical',
            default=0,
            help='Critical threshold.',
            required=False)

# Init plugin
plugin = PluginConnection(
    version="1.1.0",
    description="Check number of connection on ebc.vxuser table.")

plugin.shortoutput = "The number of connections in the ebc.vxuser " \
                     "table is {nbconn}."

cmd = """echo "echo \\"select count(*) \
from ebc.vxuser \
where connected != '0';\\" \
|sqlplus {0}/{1}@{2}" \
|sudo ORACLE_HOME={3} -i -u {4} \
|sed -n '/--/{{n; p;}}'""".format(plugin.options.oracle_db_user,
                                  plugin.options.oracle_db_password,
                                  plugin.options.oracle_sid,
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
    status = plugin.ok
    logger.debug("Result: {}".format(result))

    # Check threshold
    if plugin.options.warning:
        if result >= plugin.options.warning:
            status = plugin.warning

    if plugin.options.critical:
        if result >= plugin.options.critical:
            status = plugin.critical

    # Output and status to Nagios
    status(plugin.output({"nbconn": result}))
except plugin.ssh.SSHError as ssh_error_msg:
    plugin.shortoutput = "SSH error: {}".format(ssh_error_msg)
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())
except Exception:
    plugin.shortoutput = "Something unexpected happened ! " \
                         "Please investigate..."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())
