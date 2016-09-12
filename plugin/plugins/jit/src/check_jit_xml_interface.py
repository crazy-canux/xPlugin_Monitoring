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

# Std imports
import logging
from datetime import datetime
from monitoring.nagios.utilities import humanize_duration

# Plugin imports
import jit
from jit.plugin import XMLStatusCheck


# Logging
logger = logging.getLogger('plugin.xml')
logger.debug("Starting...")

# Init plugin
plugin = XMLStatusCheck(version=jit.VERSION,
                        description='Check that the XML interface file is kept '
                                    'updated.')

# Main
status = None

now = datetime.utcnow()
xml_age = humanize_duration(now - plugin.interface.last_updated, show=[
    'days', 'hours', 'minutes'])
logger.debug('XML interface file age: %s', xml_age['timedelta'])

# Check thresholds
if xml_age['timedelta'] >= plugin.options.critical_mins:
    logger.debug('Above limit ! Set to %s.', plugin.options.critical_mins)
    status = plugin.critical
    plugin.shortoutput = "The XML has not been updated since {as_string} ! " \
                         "(>= {0.critical_mins}). " \
                         "Using version {1.version}.".format(plugin.options,
                                                             plugin.interface,
                                                             **xml_age)
else:
    status = plugin.ok
    plugin.shortoutput = "XML interface file is up-to-date. " \
                         "Using version {0.version}.".format(plugin.interface)

# Return status and output to Nagios
if status:
    status(plugin.output())
else:
    plugin.critical('Unexpected error during plugin execution. '
                    'Application state could not be verified !')
