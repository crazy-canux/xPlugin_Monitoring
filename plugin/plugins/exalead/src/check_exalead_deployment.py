#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
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

import logging
from xml.etree.ElementTree import ElementTree

from exalead import VERSION
from exalead.plugin import ExaleadDeployment


logger = logging.getLogger("plugin")

# MAIN
#
plugin = ExaleadDeployment(description='Check Exalead deployment states.',
                           version=VERSION)
xml_data = plugin.getXMLData()

# Store Nagios output and number of instance in error
alert = 0
nagios_output = ""
nagios_longoutput = ""
nagios_status = None

# XML Processing
logger.debug('Processing XML data:')
xml_tree = ElementTree()
xml_tree.parse(xml_data)
xml_HostStatus = xml_tree.findall(
    "{deployment}HostStatus".format(**plugin.xml_namespaces))

# Iterate over host status list
for host in xml_HostStatus:
    hostname = host.get('hostname')
    instance_name = host.get('install').title()
    xml_ProcessStatus = host.findall(
        "{deployment}ProcessStatus".format(**plugin.xml_namespaces))

    logger.debug('\tFound host instance: {0}'.format(hostname))
    logger.debug('\t\tInstance name: {0}'.format(instance_name))

    # Check processes states for current host
    for pos, process in enumerate(xml_ProcessStatus):
        process_name = process.get('processName')
        process_status = process.get('status')

        logger.debug('\t\tProcess: {0} ({1})'.format(process_name,
                                                     process_status))

        if process_status != "started":
            if not pos:
                nagios_longoutput += \
                    '\n==== {0} ({1}) ====\n\n'.format(hostname, instance_name)

            nagios_longoutput += \
                '* Process: {0} is in {1} state ! *\n'.format(process_name,
                                                              process_status)
            alert += 1

# Format Nagios output
if alert == 1:
    nagios_output = '{0} process is not started !'.format(alert)
    nagios_status = plugin.warning
elif alert > 1:
    nagios_output = '{0} processes are not started !'.format(alert)
    nagios_status = plugin.warning
else:
    nagios_output = 'All processes are running.'
    nagios_status = plugin.ok

# Return message and status to Nagios
nagios_output += nagios_longoutput
raise nagios_status(nagios_output)
