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

import logging
import datetime

from xml.etree.ElementTree import ElementTree

from exalead import VERSION
from exalead.plugin import ExaleadBuildGroup


logger = logging.getLogger('plugin')

# MAIN
#
plugin = ExaleadBuildGroup(description='Check Exalead buildgroup state.',
                           version=VERSION)
xml_data = plugin.getXMLData()

# Store Nagios output and number of instance in error
alert = 0
nagios_output = ""
nagios_longoutput = ""
nagios_perfdata = " | "
nagios_status = None

# XML Processing
logger.debug('Processing XML data:')
xml_tree = ElementTree()
xml_tree.parse(xml_data)
xml_IndexSliceInstanceStatus = xml_tree.findall(
    "{buildgroup}IndexSliceInstanceStatus".format(**plugin.xml_namespaces))

# Sum all instances values with the same name
instances = {}
for available_instance in xml_IndexSliceInstanceStatus:
    name = available_instance.get('sliceInstance')
    last_commit_str = available_instance.get('lastCommit')

    stats = instances.setdefault(name, {"ndocs": 0, "last_commit": []})
    stats["ndocs"] += int(available_instance.get('ndocs'))

    if last_commit_str:
        try:
            last_commit = datetime.datetime.strptime(last_commit_str,
                                                     '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise plugin.unknown('Error during last commit date conversion !')
        else:
            stats["last_commit"].append(last_commit)

    instances[name].update(stats)

# Create instance status table
for name, stats in instances.viewitems():
    ndocs = int(stats["ndocs"])
    try:
        last_commit = max(stats["last_commit"])
    except ValueError:
        last_commit = None

    logger.debug('\tFound instances: {0}'.format(name))
    logger.debug('\t\tInstance Ndocs: {0}'.format(ndocs))
    logger.debug('\t\tInstance Last Commit: {0}'.format(last_commit))

    # Do thresholds checking
    if ndocs <= plugin.limit_ndocs:
        alert += 1
        nagios_longoutput += \
            '\n* Instance {0}: ndocs below threshold. ' \
            'Value: {1} (<{2}) *'.format(name.title(),
                                         ndocs, plugin.limit_ndocs)
    if last_commit:
        commit_age = plugin.calc_commit_age(last_commit)
        if commit_age > plugin.limit_commit_age:
            alert += 1
            nagios_longoutput += \
                '\n* Instance {0}: last commit above threshold. ' \
                'Value: {1} (>{2}) *'.format(name.title(),
                                             last_commit,
                                             plugin.limit_commit_age)

    nagios_perfdata += "\'{}\'={};{};;0;{}; ".format(name.title(),
                                                     ndocs,
                                                     plugin.limit_ndocs,
                                                     ndocs+500)

logger.debug('Instance in error: {0}'.format(alert))

# Format Nagios output
if alert:
    nagios_output = '{0} error for buildgroup {1} !'.format(alert,
                                                            plugin.buildgroup)
    nagios_status = plugin.warning
else:
    nagios_output = 'Buildgroup {0} status is clean.'.format(plugin.buildgroup)
    nagios_status = plugin.ok

# Return message and status to Nagios
nagios_output += nagios_longoutput + nagios_perfdata
raise nagios_status(nagios_output)
