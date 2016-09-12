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
import traceback

import requests
import re
from generic.version import VERSION
from monitoring.nagios.plugin import NagiosPlugin
from generic.parser.json import JSONParser
from generic.parser.exceptions import RawValueNameError


# Initialize default logger
logger = logging.getLogger("plugin.default")


# Customize plugin here
class CustomPlugin(NagiosPlugin):
    """
    Customize Plugin definition.
    """
    def define_plugin_arguments(self):
        super(CustomPlugin,self).define_plugin_arguments()

        self.required_args.add_argument('-w', '--warn',
                                        type=int,
                                        dest='warning',
                                        default=0,
                                        help='Warning threshold.',
                                        required=False)

        self.required_args.add_argument('-c', '--crit',
                                        type=int,
                                        dest='critical',
                                        default=0,
                                        help='Critical threshold.',
                                        required=False)

        self.required_args.add_argument('-P', '--port',
                                        type=int,
                                        dest='port',
                                        default=80,
                                        help='Port on which to communicate to (default is 80).',
                                        required=False)

        self.required_args.add_argument('-p', '--path',
                                        dest='path',
                                        help='the remaining URL part as /path/to/json/data.json.',
                                        required=True)

        self.required_args.add_argument('-k', '--key',
                                        dest='key',
                                        help='the key to process.',
                                        required=True)

        self.required_args.add_argument('-S', '--ssl',
                                        action='store_true',
                                        dest='ssl',
                                        help='to set the connection to HTTPS instead of HTTP (disabled by default).',
                                        required=False)



# Initialize the plugin
plugin = CustomPlugin(version=VERSION, description="Parse JSON data via HTTP.")

if not re.search('^/.*\.json$', plugin.options.path):
    plugin.shortoutput = "Error Path '{0}' no valid!!".format(plugin.options.path)
    plugin.longoutput.append('Path = The remaining URL part as /path/to/json/data.json.')
    plugin.unknown(plugin.output())


try:
    # Plugin execution code goes here.
    logger.debug("Plugin execution started...")

    ssl=""
    if plugin.options.ssl:
        ssl="s"

    url="http{ssl}://{host}:{port}{path}".format(host=plugin.options.hostname,
                                                 path=plugin.options.path,
                                                 port=plugin.options.port,
                                                 ssl=ssl)
    logger.debug(url)
    json_request = requests.get(url)

    json_data = json_request.text
    logger.debug(json_data)

    json_parser = JSONParser(json_data)

    try:
        value=json_parser[plugin.options.key]
        logger.debug(value)
    except RawValueNameError as e:
        plugin.shortoutput = e.message
        plugin.longoutput = traceback.format_exc().splitlines()
        plugin.unknown(plugin.output())

    status=plugin.ok
    plugin.shortoutput = "{key} : {value}".format(key=plugin.options.key,
                                                 value=value)
    plugin.longoutput = json_parser.longoutput
    plugin.perfdata.append('{key}={value};{warn};{crit};0;'.format(key=plugin.options.key,
                                                                   value=value,
                                                                   warn=plugin.options.warning,
                                                                   crit=plugin.options.critical))

    # Check threshold
    threshold=0
    if plugin.options.warning:
        if value >= plugin.options.warning:
            status = plugin.warning
            threshold=plugin.options.warning
    if plugin.options.critical:
        if value >= plugin.options.critical:
            status = plugin.critical
            threshold=plugin.options.critical

    if threshold:
        plugin.shortoutput += " >= {0}".format(threshold)

    status(plugin.output())

except Exception:
    plugin.shortoutput = "Unexpected plugin behavior ! Traceback attached."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())
