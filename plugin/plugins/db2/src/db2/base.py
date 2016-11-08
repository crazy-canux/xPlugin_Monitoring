# -*- coding: utf-8 -*-
# Copyright (C) Canux <http://www.Company.com/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Base classes for all DB2 plugins."""

import logging
import traceback

from monitoring.nagios.plugin import NagiosPluginSSH


class BasePlugin(NagiosPluginSSH):
    """Base class for all DB2 plugins."""
    def __init__(self, *args, **kwargs):
        super(BasePlugin, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('plugin.db2')

    def run(self):
        """Run the plugin."""
        try:
            self.main()
        except Exception:
            self.shortoutput = 'Unexpected plugin error ! Please investigate.'
            self.longoutput = traceback.format_exc().splitlines()
            self.unknown(self.output())

    def main(self):
        """Main entry point for the plugin."""
        raise NotImplementedError('Main entry point is not implemented !')

    def define_plugin_arguments(self):
        """Default set of plugin arguments for all plugins."""
        super(BasePlugin, self).define_plugin_arguments()
        self.required_args.add_argument('-d', '--db2user',
                                        dest="db2_user",
                                        help="Db2 user use, an string",
                                        required=True)

    def run_command(self, cmd):
        """
        Run the specified command on remote host using SSH and get its output.
        """
        self.logger.debug("run command: {0}".format(cmd))

        try:
            command = self.ssh.execute(cmd)
            output = command.output
            errors = command.errors

            if not any(output):
                self.unknown("No output from command execution ! ".format(
                    command.status))
            if errors:
                self.unknown("Errors found in command execution ! "
                             "Return code is {0}.\n{1}".format(
                                 command.status, "\n".join(errors)))

            self.logger.debug("Command output: {0}".format("\"".join(output)))

            return output
        except self.ssh.SSHCommandTimeout:
            self.unknown("SSH command has reached timeout "
                         "set to {} secs !".format(self.options.timeout))
        except self.ssh.SSHError:
            self.unknown("Error during the execution of the db2 command !"
                         "Please investigate.")
        except Exception:
            self.unknown("Error during the execution of the db2 command !"
                         "Please investigate.")
