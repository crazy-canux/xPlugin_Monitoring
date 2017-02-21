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

# Std imports
import logging

# Plugin imports
import jit

from jit import exceptions
from jit.plugin import XMLEventPlugin


logger = logging.getLogger('plugin.event')

# Init plugin
plugin = XMLEventPlugin(version=jit.VERSION,
                        description='Check a specific event status from the '
                                    'XML.')

# Main
status = None


try:
    role = plugin.interface.role.upper()
    logger.debug("Role {0}" . format(role))
    if role != "MAIN":
        plugin.ok('The servers role \"%s\" is not "MAIN"! ' % role)
    jit_event = plugin.interface[plugin.options.event]
    status = jit_event.severity
    plugin.shortoutput = jit_event.message
    plugin.longoutput = jit_event.details
except exceptions.EventNotFound:
    plugin.unknown('No event \"%s\" found ! '
                   'Check syntax.' % plugin.options.event)

# Return status and output to Nagios
if status:
    status(plugin, plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution ! Should debug.')
