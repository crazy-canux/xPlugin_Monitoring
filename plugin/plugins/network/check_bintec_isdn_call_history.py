#!/usr/bin/env python

################################################################################
#
# check_bintec_isdn_call_history.py
#
# Usage: check_bintec_isdn_call_history.py [-h] [--debug] [--version]
#                                           -H HOSTNAME
#
# Create: 24/09/2013
# Author: CREMET Adrien
#
# Modify: JJ/MM/AAAA
# Author:
# Object:
#
################################################################################

import logging as log
import re
import datetime


from monitoring.nagios.plugin import NagiosPluginSNMP

logger = log.getLogger('plugin')

# The main procedure
desc_plug = "This plugin returns the isdnCallHistory table."
plugin = NagiosPluginSNMP(version=0.1, description=desc_plug)

oid = {
    'isdnCallHistoryType': '1.3.6.1.4.1.272.4.2.8.1.2',
    'isdnCallHistoryTime': '1.3.6.1.4.1.272.4.2.8.1.3',
    'isdnCallHistoryDuration': '1.3.6.1.4.1.272.4.2.8.1.4',
    'isdnCallHistoryRemoteNumber': '1.3.6.1.4.1.272.4.2.8.1.8',
}

call_type = {
    1: 'Incoming',
    2: 'Outgoing',
}
query = plugin.snmp.getnext(oid)

# Store temp data
temp_data = []
size_rm = 0
size_rm_big = 0

if query.has_key('isdnCallHistoryType'):
    for status in query['isdnCallHistoryTime']:
        isdnCallHistory_Type = [e.pretty() for e in query['isdnCallHistoryType']
                                if e.index == status.index][0]
        isdnCallHistory_Type = call_type[int(isdnCallHistory_Type)]
        isdnCallHistory_Duration = [e.pretty() for e in query['isdnCallHistoryDuration']
                                    if e.index == status.index][0]
        isdnCallHistory_RemoteNumber = [e.pretty() for e in query['isdnCallHistoryRemoteNumber']
                                        if e.index == status.index][0]
        size_rm = len(isdnCallHistory_RemoteNumber)
        if size_rm > size_rm_big:
            size_rm_big = size_rm
        temp_data.append((datetime.datetime.fromtimestamp(status.value).strftime('%Y-%m-%d %H:%M:%S'),
                          isdnCallHistory_Type,
                          isdnCallHistory_Duration,
                          isdnCallHistory_RemoteNumber))

else:
    plugin.unknown('SNMP Query Error: query all isdnCallHistory status returned no result !')

logger.debug('Temp data: %s' % temp_data)

y = 0
z = 0
callnb = len(temp_data)
longoutput = ""
longoutput_incoming = ""
longoutput_outgoing = ""
nbincoming = 0
nboutgoing = 0
size_rm_temp = 0

## Parcours du tableau

for temp in temp_data:
    time, type, duration, remotenumber = temp
    if remotenumber == 0 or remotenumber == '':
        remotenumber = 'Not disclosed'
    size_rm_temp = ((size_rm_big - len(remotenumber) + 3 )) * ' '

# Tri par appel entrant ou sortant

    if type == "Incoming":
        nbincoming = nbincoming + 1
        if y < 1:
            longoutput_incoming += "{0} :{1}"\
                .format(str(type).upper(), '\n')
            y = y + 1
        longoutput_incoming += "  {0}   Remote number : {1}{2}Duration : {3}{4}"\
            .format(str(time), str(remotenumber), str(size_rm_temp), str(duration), '\n')
    if type == "Outgoing":
        nboutgoing = nboutgoing + 1
        if z < 1:
            longoutput_outgoing += "{0} :{1}"\
                .format(str(type).upper(), '\n')
            z = z + 1
        longoutput_outgoing += "  {0}   Remote number : {1}{2}Duration : {3}{4}"\
            .format(str(time), str(remotenumber), str(size_rm_temp), str(duration), '\n')

longoutput = longoutput_incoming + longoutput_outgoing
longoutput = longoutput.rstrip('\n')

# Output to Nagios
output = "There are : {0} calls.({1} : Incoming and {2} : Outgoing){3}"\
    .format(str(callnb), str(nbincoming), str(nboutgoing), '\n')
plugin.ok(output + longoutput)
