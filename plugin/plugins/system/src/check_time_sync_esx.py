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

"""
Plugin check_time_sync_esx.

Checks time sync between ESX host and its VM.
"""

import logging
from datetime import datetime, timedelta
from monitoring.nagios.plugin import NagiosPluginSSH

logger = logging.getLogger('plugin.ssh')


# define new args
class PluginTime(NagiosPluginSSH):
    """Customize plugin behavior."""
    def define_plugin_arguments(self):
        super(PluginTime, self).define_plugin_arguments()

        self.required_args.add_argument('-s', '--second',
                                        dest="second",
                                        type=int,
                                        help="ESX should be sync with host at "
                                             "least this number of minutes.",
                                        required=True)

plugin = PluginTime(version='0.0.1', description="Check time sync with ESX")

# Final status exit for the plugin
status = None

# Attr
esx_time_cmd = plugin.ssh.execute("vmware-toolbox-cmd stat hosttime")
local_time_cmd = plugin.ssh.execute("date '+%d %b %Y %H:%M:%S'")

if esx_time_cmd.output and local_time_cmd.output:
    esx_time_str = esx_time_cmd.output[0]
    esx_time = datetime.strptime(esx_time_str, '%d %b %Y %H:%M:%S')
    logger.debug("ESX Host time: {0}".format(esx_time))

    local_time_str = local_time_cmd.output[0]
    local_time = datetime.strptime(local_time_str, '%d %b %Y %H:%M:%S')
    logger.debug("Local VM time: {0}".format(local_time))
else:
    plugin.unknown("No output during command execution !")

diff = (local_time - esx_time).total_seconds()
diff_abs = abs(diff)
delta = timedelta(seconds=diff_abs)
logger.debug("Diff: {0}".format(delta))

# Convert second into timedelta format
sec = timedelta(seconds=plugin.options.second)

# Is the ESX sync ?
if esx_time_cmd.output and local_time_cmd.output:
    if delta < sec:
        status = plugin.ok
        plugin.shortoutput = "The ESX time is sync properly - " \
                             "Timedelta : {0}".format(delta)
    else:
        status = plugin.critical
        plugin.shortoutput = "The ESX time isn't sync properly - " \
                             "Timedelta : {0}".format(delta)
else:
    status = plugin.unknown('No output during command execution !')

# Performance data
plugin.perfdata.append('time_sync_esx={0}s;'.format(diff))

# Return status with message to Nagios
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
