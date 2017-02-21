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

logger = logging.getLogger('plugin.loop')


# define new args
class PluginLOOP(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginLOOP, self).define_plugin_arguments()

        self.required_args.add_argument('-O', '--Oracle_home',
                                        dest="oracle_home",
                                        default='/opt/oracle/ora11',
                                        help="Oracle Home",
                                        required=False)

        self.required_args.add_argument('-S', '--Oracle_SID',
                                        dest="oracle_sid",
                                        help="Oracle SID",
                                        required=False)

        self.required_args.add_argument('-o', '--User',
                                        dest="oracle_user",
                                        help="Oracle user",
                                        required=False)

        self.required_args.add_argument('-OP', '--Password',
                                        dest="oracle_password",
                                        help="Oracle Password",
                                        required=False)

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
plugin = PluginLOOP(version="1.0",
                    description="check Oracle table")
plugin.shortoutput = "check looping batches"

# Final status exit for the plugin
status = None

cmd = """\
echo ". /usr/local/bin/nrft.env ;echo \\"select e.eprentidx || ' ' || \
e.eprenttype || ' ' || nrftfmfi.FMBATCH.BATLOGNAME || ' ' || count(*) from \
nrftfmfi.fmentprop e join nrftfmfi.fmpage p on e.eprentidx=p.PAGIDX join \
nrftfmfi.fmbatch on p.BATIDX=nrftfmfi.FMBATCH.BATIDX group by \
e.eprentidx,e.eprenttype,nrftfmfi.FMBATCH.BATLOGNAME having \
count(*) > 1000;\\" \ |{0}/bin/sqlplus -s nagios/nagios_nrft" \
|sudo -u oracle -i \ \
|sed -n '/--/{{n; p;}}""".format(plugin.options.oracle_home)

logger.debug("cmd : {0}".format(cmd))

try:

    command = plugin.ssh.execute(cmd)
    output = command.output
    errors = command.errors
    status = plugin.ok

    logger.debug("Received output: %s", output)
    logger.debug("Received errors: %s", errors)

except:
    plugin.shortoutput = "Something unexpected happened ! " \
                         "Please investigate..."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())


if errors:
    plugin.unknown("Errors found:\n{}".format("\n".join(errors)))


total = len(output)
if len(output) > 0:
    status = plugin.warning
    plugin.shortoutput = "There are {0} looping batches".format(total)
    plugin.longoutput = output

else:

    status = plugin.ok
    plugin.shortoutput = "There are no looping batch"

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())

else:
    plugin.unknown('Unexpected error during plugin execution, '
                   'please investigate with debug mode on.')
