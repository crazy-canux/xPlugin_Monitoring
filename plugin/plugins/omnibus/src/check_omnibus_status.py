#!/usr/bin/env python
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

"""
Plugin check_omnibus_status.

Checks the status of OMNibus.
"""

import logging
from monitoring.nagios.plugin import NagiosPluginSSH

logger = logging.getLogger('plugin.ssh')


# Define new args
class PluginOMNIbus(NagiosPluginSSH):
    """Customize plugin behavior."""
    def define_plugin_arguments(self):
        super(PluginOMNIbus, self).define_plugin_arguments()

        self.required_args.add_argument('-i', '--instance',
                                        dest="instance",
                                        help="Name of the OMNibus Instance",
                                        required=False)

plugin = PluginOMNIbus(version='0.0.2',
                    description="Checks the status of OMNibus")

# Final status exit for the plugin
status = None

try:
    cmd = "/opt/IBM/tivoli/netcool/omnibus/bin/nco_ping {0}".format(plugin.options.instance)
    command = plugin.ssh.execute(cmd)

    output = command.output
    errors = command.errors
    logger.debug("Received output: %s", output)
    logger.debug("Received errors: %s", errors)
except:
    plugin.shortoutput = "Something unexpected happened ! Please investigate..."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())

if errors:
    plugin.shortoutput = "Errors returned during command execution !"
    plugin.longoutput = errors
    status =  plugin.unknown(plugin.output())
elif 'NCO_PING: Server available.' in output:
    plugin.shortoutput = "{0} is available.".format(plugin.options.instance)
    status =  plugin.ok(plugin.output())
elif 'NCO_PING: Server unavailable.' in output:
    plugin.shortoutput = "{0} is unavailable !".format(plugin.options.instance)
    status =  plugin.critical(plugin.output())
else:
    plugin.shortoutput = "Cannot determinate {0} status !".format(plugin.options.instance)
    status =  plugin.unknown(plugin.output())

# Return status with message to Nagios
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
