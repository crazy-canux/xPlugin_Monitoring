#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canux CHENG <canuxcheng@gmail.com>
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

from monitoring.nagios.plugin import NagiosPluginSSH

logger = logging.getLogger('plugin.sshcommand')


# define new args
class PluginSSHCommand(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginSSHCommand, self).define_plugin_arguments()
        self.required_args.add_argument("-C", "--command",
                                        dest="command",
                                        help="The command.",
                                        required=True)
        self.required_args.add_argument("-w", "--warn",
                                        type=int,
                                        dest="warning",
                                        default=0,
                                        help="Warning threshold.",
                                        required=False)
        self.required_args.add_argument("-c", "--crit",
                                        type=int,
                                        dest="critical",
                                        default=0,
                                        help="Critical threshold.",
                                        required=False)

# Init plugin
plugin = PluginSSHCommand(version="1.0.0",
                          description="Run a ssh command and return value.")

# Final status exit for the plugin
status = None

try:
    cmd = plugin.options.command
    logger.debug("cmd : {0}".format(cmd))
    command = plugin.ssh.execute(cmd)
    output = command.output
    errors = command.errors
    logger.debug("Received output: {}".format(output))
    logger.debug("Received errors: {}".format(errors))

    if errors:
        plugin.unknown("Errors found:\n{}".format("\n".join(errors)))

    if not any(output):
        plugin.unknown("No output from command execution ! ".format(
            command.status))

    # Check the result of the command.
    result = int(output.pop())
    logger.debug("Result: {}".format(result))
    status = plugin.ok

    # Check threshold
    if plugin.options.warning:
        if result >= plugin.options.warning:
            status = plugin.warning
    if plugin.options.critical:
        if result >= plugin.options.critical:
            status = plugin.critical

    # Output for nagios.
    plugin.shortoutput = "The result is {}.".format(result)
    plugin.perfdata.append("{table}={value};{warn};{crit};0;".format(
        crit=plugin.options.critical,
        warn=plugin.options.warning,
        value=result,
        table=plugin.options.command.lower()))

    # Exit the plugin normal.
    status(plugin.output())
    logger.debug("Return status and exit to Nagios.")

except plugin.ssh.SSHError as ssh_error_msg:
    plugin.shortoutput = "SSH error: {}".format(ssh_error_msg)
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())
except Exception:
    plugin.shortoutput = "Something unexpected happened! " \
        "Please investigate..."
    plugin.longoutput = traceback.format_exc().splitlines()
    plugin.unknown(plugin.output())
