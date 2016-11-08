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

from monitoring.nagios.plugin import NagiosPluginSSH


logger = logging.getLogger("plugin.fs_readonly")


class PluginWriteable(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginWriteable, self).define_plugin_arguments()
        self.required_args.add_argument("-f", "--folder",
                                        dest="folder",
                                        help="Specify one folder.")

plugin = PluginWriteable(version='2.0.1',
                         description="Check writeable status of fs.")

# Final status exit for the plugin
status = None

# Attrs
if plugin.options.folder:
    cmd = "awk '$3 !~ /iso9660/ && $4 ~ /(^|,)ro($|,)/' /proc/mounts | \
    grep %s" % plugin.options.folder
else:
    cmd = "awk '$3 !~ /iso9660/ && $4 ~ /(^|,)ro($|,)/' /proc/mounts"

logger.debug("cmd: {}".format(cmd))
command = plugin.ssh.execute(cmd)
logger.debug("Remote command output:\n%s", "\n".join(command.output))
nbOut = len(command.output)

if not command.output:
    status = plugin.ok
    plugin.shortoutput = "All filesystems are writable"

if command.output:
    status = plugin.critical
    plugin.shortoutput = "{0} filesystems are readable only".format(nbOut)
    plugin.longoutput = command.output

# Return status with message to Nagios
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
