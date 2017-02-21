#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_cisco_psu.py
# Author        : Canux CHENG
# Description   : Check all PSU on Cisco. Alert if one is no ON.
#-------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================
#
#

import logging as log
import re

from shared import __version__
from monitoring.nagios.plugin import NagiosPluginSNMP

logger = log.getLogger('plugin')


# The main procedure
progdesc = 'Check all PSU of Cisco and alert if one is not on.'

plugin = NagiosPluginSNMP(version=__version__, description=progdesc)

oids = {
    'psu_status': '1.3.6.1.4.1.9.9.117.1.1.2.1.2', # From CISCO-ENTITY-FRU-CONTROL-MIB
    'psu_descs': '1.3.6.1.2.1.47.1.1.1.1.2', # From ENTITY-MIB
}

desc = {
    1: 'offEnvOther',
    2: 'on',
    3: 'offAdmin',
    4: 'offDenied',
    5: 'offEnvPower',
    6: 'offEnvTemp',
    7: 'offEnvFan',
    8: 'failed',
    9: 'onButFanFail',
    10: 'offCooling',
    11: 'offConnectorRating',
    12: 'onButInlinePowerFail',
}

query = plugin.snmp.getnext(oids)

# Store temp data
temp_data = []

if query.has_key('psu_status'):
    for status in query['psu_status']:
        psu_name = [e.pretty() for e in query['psu_descs'] if e.index == status.index][0]
        temp_data.append((str(status.index), psu_name, status.value))
else:
    plugin.unknown('SNMP Query Error: query all psu status returned no result !')

logger.debug('Temp data: %s' % temp_data)

# Check thresholds and format output to Nagios
longoutput = ""
longoutput_error = ""
longoutput_ok = ""
output = ""
exit_code = 0
nbr_error = 0
nbr_ok = 0
count = 0


for temp in temp_data:
    count += 1
    temp_index, temp_descr, temp_value = temp

    if not re.search(r'470$', temp_index) and not re.search(r'471$', temp_index):
        continue

    if not desc.has_key(temp_value):
        plugin.unknown("Unsupported status code \"{}\" !".format(temp_value))

    if temp_value != 2:
        exit_code = 2
        nbr_error += 1
        if re.search(r'470$', temp_index):
            longoutput_error += ' * %s: (PSU1) (%d) %s *\n' % (temp_descr, temp_value, desc[temp_value])
        elif re.search(r'471$', temp_index):
            longoutput_error += ' ** %s: (PSU2) (%d) %s **\n' % (temp_descr, temp_value, desc[temp_value])
    else:
        nbr_ok += 1
        if re.search(r'470$', temp_index):
            longoutput_ok += ' %s: (PSU1) %s\n' % (temp_descr, desc[temp_value])
        elif re.search(r'471$', temp_index):
            longoutput_ok += ' %s: (PSU2) %s\n' % (temp_descr, desc[temp_value])

# Format output
if nbr_error > 0:
    longoutput += 'ERROR: %d\n%s\n' % (nbr_error, longoutput_error)
if nbr_ok > 0:
    longoutput += 'ON: %d\n%s\n' % (nbr_ok, longoutput_ok)


# Output to Nagios
longoutput = longoutput.rstrip('\n')
if exit_code == 2:
    output = '%d PSU : ERROR !\n' % nbr_error
    plugin.critical(output + longoutput)
elif not exit_code:
    output = 'All PSU are ON.\n'
    plugin.ok(output + longoutput)
