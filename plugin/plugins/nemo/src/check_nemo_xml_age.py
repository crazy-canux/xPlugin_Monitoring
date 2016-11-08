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

import logging
import nemo
from nemo.xml import NemoPluginXmlAge
from datetime import datetime

logger = logging.getLogger('plugin.base')

# Init plugin
plugin = NemoPluginXmlAge(version=nemo.__version__, description="Check XML age" )

# Final status exit for the plugin
status = None

#Attrs
current_date = datetime.utcnow()
xml_timestamp = int(plugin.xml.find('timestamp').text)
xml_age = datetime.utcfromtimestamp(xml_timestamp)
age = current_date - xml_age

#Loggers
logger.debug("Current UTC Date: {0}".format(current_date))
logger.debug("XML timestamp (epoch UNIX) : {0}".format(xml_timestamp))
logger.debug("XML last update: {0} UTC".format(xml_age))
logger.debug("XML age: {0} UTC".format(age))

#Is the XML outdated ?
if xml_timestamp:
    if age < plugin.options.max_age:
        status = plugin.ok
        plugin.shortoutput = "The XML file is updated - Last update : {0} UTC".format(xml_age)
    else:
        status = plugin.critical
        plugin.shortoutput = "The XML file is outdated - Last update : {0} UTC".format(xml_age)
else:
    status = plugin.unknown('Timestamp not found !')

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
