#!/usr/bin/env python
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

"""
Plugin check_optim_xml_age.

Checks the age of the XML file.
"""

import logging
from datetime import datetime, timedelta
from monitoring.nagios.plugin import NagiosPluginHTTP

logger = logging.getLogger('plugin')

# Define new args
class PluginOptim(NagiosPluginHTTP):
    """Customize plugin behavior."""
    def define_plugin_arguments(self):
        super(PluginOptim, self).define_plugin_arguments()

        self.required_args.add_argument('-w', '--warning',
                                        dest="warning",
                                        type=int,
                                        help="File should be updated before "
                                             "this number of days.",
                                        default=8,
                                        required=False)
        self.required_args.add_argument('-c', '--critical',
                                        dest="critical",
                                        type=int,
                                        help="File should be updated before "
                                             "this number of days.",
                                        default=15,
                                        required=False)

plugin = PluginOptim(version="1.0",
                     description="Checks the age of the XML file.")

# Final status exit for the plugin
status = None

# HTTP GET query
response = plugin.http.get(plugin.options.path)
logger.debug("Received output:\n<!--start-->\n%s\n<!--end-->", response.content)

# Attr
xml_data = response.xml()
last_update_str = xml_data.alert.last_update.contents[0]
utc_now = datetime.utcnow()
logger.debug("Current date: %s", utc_now)

# Convert data last_update into datetime format
if last_update_str:
    last_update = datetime.strptime(last_update_str, '%Y%m%d%H%M%S%f')
    logger.debug("Last update: %s", last_update)
else:
    plugin.unknown("No output during command execution !")

# Calculate timedelta between utc_now and date last_update
diff = (utc_now - last_update).total_seconds()
diff_abs = abs(diff)
diff_in_days = diff_abs / 86400
delta = timedelta(days=diff_in_days)
logger.debug("Diff: {0}".format(delta))

# Convert arguments into timedelta format
warn = timedelta(days=plugin.options.warning)
crit = timedelta(days=plugin.options.critical)

# Is XML updated ?
if last_update_str:
    if delta < warn:
        status = plugin.ok
        plugin.shortoutput = "The XML is up to date - " \
                             "Timedelta : {0}".format(delta)
    elif warn <= delta <= crit:
        status = plugin.warning
        plugin.shortoutput = "The XML isn't up to date - " \
                             "Timedelta : {0}".format(delta)
    else:
        status = plugin.critical
        plugin.shortoutput = "The XML isn't up to date - " \
                             "Timedelta : {0}".format(delta)
else:
    status = plugin.unknown('No output during command execution !')

# Return status with message to Nagios
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
