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
Plugin check_ad_xml_age.

Checks the age of the XML file.
"""

import logging
from datetime import datetime, timedelta
from monitoring.nagios.plugin import NagiosPluginHTTP
import traceback

logger = logging.getLogger('plugin')


# Define new args
class PluginAd2012(NagiosPluginHTTP):
    """Customize plugin behavior."""
    def define_plugin_arguments(self):
        super(PluginAd2012, self).define_plugin_arguments()

        self.required_args.add_argument('-w', '--warning',
                                        dest='warning',
                                        type=int,
                                        help='File should be updated before '
                                             'this number of minutes.',
                                        default=1,
                                        required=False)
        self.required_args.add_argument('-c', '--critical',
                                        dest='critical',
                                        type=int,
                                        help='File should be updated before '
                                             'this number of minutes.',
                                        default=5,
                                        required=False)

plugin = PluginAd2012(version='1.1.0',
                      description='Checks the age of the XML file.')

# Final status exit for the plugin
status = None

try:
    # HTTP GET query
    response = plugin.http.get(plugin.options.path)
    # logger.debug("Received output:\n%s", response.content)

    # Attr
    data = response.xml()
    server_tag = data.find_all('server')[0]
    last_update_str = server_tag['timestamp']
    utc_now = datetime.utcnow()
    logger.debug('Current date: %s', utc_now)
except Exception:
    plugin.shortoutput = "Something unexpected happend in " \
        "checkmode_decimal. Please investigate..."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())


# Convert last_update_str into datetime format
if last_update_str:
    last_update = datetime.utcfromtimestamp(
        float(last_update_str.replace(',', '.')))
    logger.debug('Last update: %s', last_update)
else:
    plugin.unknown('No output during command execution !')

# Calculate timedelta between utc_now and date last_update
diff = (utc_now - last_update).total_seconds()
diff_abs = abs(diff)
diff_in_minutes = diff_abs / 60
delta = timedelta(minutes=diff_in_minutes)
logger.debug('Diff: {0}'.format(delta))

# Convert arguments into timedelta format
warn = timedelta(minutes=plugin.options.warning)
crit = timedelta(minutes=plugin.options.critical)

# Is XML updated ?
if last_update_str:
    if delta < warn:
        status = plugin.ok
        plugin.shortoutput = 'The XML is up to date - ' \
                             'Timedelta : {0}'.format(delta)
    elif warn <= delta <= crit:
        status = plugin.warning
        plugin.shortoutput = 'The XML is not up to date - ' \
                             'Timedelta : {0}'.format(delta)
    else:
        status = plugin.critical
        plugin.shortoutput = 'The XML is not up to date - ' \
                             'Timedelta : {0}'.format(delta)
else:
    status = plugin.unknown('No output during command execution !')

# Return status with message to Nagios
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
