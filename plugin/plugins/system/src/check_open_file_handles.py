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

__version__ = "1.1.30"

import logging
from monitoring.nagios.plugin import NagiosPluginSSH

logger = logging.getLogger('plugin.unix')


# define new args
class PluginCFile(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginCFile, self).define_plugin_arguments()
        self.required_args.add_argument('-n', '--process',
                                        dest="process",
                                        help="process to check, an string",
                                        default="gearmand",
                                        required=False)
        self.required_args.add_argument('-w',
                                        dest="warning",
                                        type=int,
                                        help="This is our warning threshold, "
                                             "an integer.",
                                        default=0,
                                        required=False)
        self.required_args.add_argument('-c',
                                        dest="critical",
                                        type=int,
                                        help="This is our critical threshold, "
                                             "an integer.",
                                        default=0,
                                        required=False)

    def verify_plugin_arguments(self):
        super(PluginCFile, self).verify_plugin_arguments()
        # Checking if warning thresholds is not > critical
        if self.options.warning > self.options.critical:
            self.unknown('Warning cannot be greater than critical !')

# Init plugin
plugin = PluginCFile(version=__version__, description="Check Open File Handles")


# Final status exit for the plugin
status = None

cmd = "sudo lsof -p $(pidof {0})".format(plugin.options.process)


logger.debug("cmd : {0}".format(cmd))

command = plugin.ssh.execute(cmd)
output = command.output
errors = command.errors

num_opened_files = len(output)
output_pattern = "Process {opt.process} has {nfiles} opened file handles."
perfdata_pattern = "open_file_handles={nfiles};{opt.warning};{opt.critical};0;"

if output:
    status = plugin.ok
    if plugin.options.warning:
        if num_opened_files >= plugin.options.warning:
            status = plugin.warning
    if plugin.options.critical:
        if num_opened_files >= plugin.options.critical:
            status = plugin.critical

    plugin.perfdata.append(perfdata_pattern.format(nfiles=num_opened_files,
                                                   opt=plugin.options))
    plugin.shortoutput = output_pattern.format(nfiles=num_opened_files,
                                               opt=plugin.options)
    plugin.longoutput = output

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')

