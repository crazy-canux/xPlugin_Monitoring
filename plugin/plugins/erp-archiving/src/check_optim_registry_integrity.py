#!/usr/bin/env python
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

"""
Plugin check_optim_registry_integrity.

Checks the integrity of the registry.
"""

import logging
from monitoring.nagios.plugin import NagiosPluginHTTP

logger = logging.getLogger('plugin')

plugin = NagiosPluginHTTP(version="1.0",
                          description="Checks the integrity of the registry.")

# Final status exit for the plugin
status = None

# HTTP GET query
response = plugin.http.get(plugin.options.path)
logger.debug("Received output:\n<!--start-->\n%s\n<!--end-->", response.content)

# Attr
xml_data = response.xml()
return_code = xml_data.alert.return_code.contents[0]
message = xml_data.alert.message.contents[0]
logger.debug("Code: %s", return_code)
logger.debug("Message: %s", message)

# Is registry integrity successfully checked ?
if return_code and message:
    if return_code == "0":
        status = plugin.ok
        plugin.shortoutput = "{0}".format(message)
    else:
        status = plugin.critical
        plugin.shortoutput = "{0}".format(message)
else:
    status = plugin.unknown('No output during command execution !')

# Return status with message to Nagios
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
