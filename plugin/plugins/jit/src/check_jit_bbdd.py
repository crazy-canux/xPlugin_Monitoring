#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (C) Canux <http://www.Company.com/>
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
from pprint import pformat
from monitoring.nagios.logger import debug_multiline

# Plugin imports
import jit
from jit.bbdd import BBDDCheck


logger = logging.getLogger('plugin.bbdd')
logger.debug("Starting...")

# Init plugin
plugin = BBDDCheck(version=jit.VERSION,
                   description='Check the size of a JIT database file. '
                               'Either database or log files can be checked.')
plugin.shortoutput = "BBDD: {files_usage} {threshold}"

# Query the database size
logger.debug("Querying the database...")
db_size = plugin.get_db_size()
debug_multiline(pformat(db_size))

# Final status exit for the plugin
status = None

# Keys used to substitute values in Nagios output
output_vars = {
    'files_usage': [],
    'threshold': "",
}

# Filter out unwanted file types
filename = ""
for key, stats in db_size.viewitems():
    if stats['type'] == plugin.options.dbfile:
        filename = key

try:
    used = db_size[filename]['size'] / 1024 / 1024  # Convert to mega-bytes
except KeyError as e:
    used = None
    plugin.unknown("Cannot find database file \"{}\"".format(filename))

# Check thresholds
logger.debug("Checking thresholds for \"{0}\"...".format(filename))
logger.debug("\t{0}: {1} MB"
             "\tWarning: {2.warning} MB"
             "\tCritical: {2.critical} MB".format(filename,
                                                  used, plugin.options))

if plugin.options.warning and plugin.options.critical:
    if plugin.options.warning <= used <= plugin.options.critical:
        logger.debug("\tStatus: WARNING")
        status = plugin.warning if not status else status
        output_vars['threshold'] = "(>= {0.warning} MB, " \
                                   "< {0.critical} MB)".format(plugin.options)
    elif used >= plugin.options.critical:
        logger.debug("\tStatus: CRITICAL")
        status = plugin.critical if not status else status
        output_vars['threshold'] = "(>= {0.critical} MB)".format(plugin.options)
    else:
        logger.debug("\tStatus: OK")
        status = plugin.ok if not status else status
        output_vars['threshold'] = "(< {0.warning} MB)".format(plugin.options)
else:
    logger.debug("\tStatus: OK")
    status = plugin.ok if not status else status
    plugin.options.warning = 0
    plugin.options.critical = 0
    output_vars['threshold'] = "(INFO)"

# Add infos to output
output_vars['files_usage'].append("{0} {1} MB".format(filename, used))
plugin.perfdata.append('{file}={value}B;{warn};{crit};0;{maxsize};'.format(
    warn=plugin.options.warning * 1024,
    crit=plugin.options.critical * 1024,
    file=filename.lower().replace('.', '_'),
    value=db_size[filename]['size'],
    maxsize=db_size[filename]['maxsize'] if not -1 else int(
        db_size[filename]['size']*1.2)))

output_vars['files_usage'] = ", ".join(output_vars['files_usage'])

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output(output_vars))
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
