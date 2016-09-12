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
from pprint import pformat

from monitoring.nagios.logger import debug_multiline

# Plugin imports
import jit
from jit.sysdb_data import SysDbDataCheck


logger = logging.getLogger('plugin.sysdb_data')
logger.debug("Starting...")

# Init plugin
plugin = SysDbDataCheck(version=jit.VERSION,
                        description='Check status of all MSSQL databases.')
plugin.shortoutput = "SYSDB_DATA: {databases_status}"

# Query the database size
logger.debug("Querying the database...")
db_status = plugin.get_all_db_status()
debug_multiline(pformat(db_status))

# Final status exit for the plugin
status = None

# Keys used to substitute values in Nagios output
output_vars = {
    'databases_status': [],
}

for db in db_status:
    name, state = db

    # Check thresholds
    logger.debug("Checking thresholds for \"{0}\"...".format(name))
    logger.debug("\t{0}: {1}".format(name, state))

    if not 'ONLINE' in state:
        logger.debug("\tStatus: CRITICAL")
        status = plugin.critical
    else:
        logger.debug("\tStatus: OK")
        status = plugin.ok

    # Add infos to output
    output_vars['databases_status'].append("{0} {1}".format(name, state))

output_vars['databases_status'] = ", ".join(output_vars['databases_status'])

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output(output_vars))
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
