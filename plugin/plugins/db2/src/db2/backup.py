# -*- coding: utf-8 -*-
# Copyright (c) Faurecia <http://www.faurecia.com/>
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

from datetime import datetime

from monitoring.nagios.plugin import argument

from .base import BasePlugin


class CheckBackup(BasePlugin):
    """Plugin to check the DB2 backup online status."""
    def define_plugin_arguments(self):
        super(CheckBackup, self).define_plugin_arguments()
        self.required_args.add_argument('-w', '--warn',
                                        type=argument.hours,
                                        dest='warning',
                                        default=0,
                                        help='Warning threshold.',
                                        required=False)

        self.required_args.add_argument('-c', '--crit',
                                        type=argument.hours,
                                        dest='critical',
                                        default=0,
                                        help='Critical threshold.',
                                        required=False)

    def main(self):
        """Main plugin execution."""
        self.shortoutput = "Backup full online (<24h)"

        now = datetime.now()

        # Final status exit for the plugin
        status = None

        cmd = \
            """echo \"db2 """ \
            """\\"SELECT unique(END_TIME) FROM SYSIBMADM.DB_HISTORY """ \
            """WHERE COMMENT like \'%ONLINE%\' and SQLCODE is null """ \
            """order by end_time desc\\"\" """ \
            """| sudo -u {0} -i """ \
            """| sed -n \'/--/{{n; p;}}\' """ \
            """| sed \'s/[ ][ ]*//g\'""".format(self.options.db2_user)

        output = self.run_command(cmd)

        # Travel output cmd by line
        cmpt = 0
        for line in output:
            self.logger.debug(line)

            status = self.ok
            end_time = datetime.strptime(line.strip(), '%Y%m%d%H%M%S')

            delta_time = now - end_time
            hours, remains = divmod(int(delta_time.total_seconds()), 3600)
            minutes, remains = divmod(remains, 60)

            self.logger.debug("end_time : {}".format(end_time))

            self.perfdata.append('backup[{0}]={1}s;{2};{3};0;'.format(
                cmpt,
                int(delta_time.total_seconds()),
                int(self.options.warning.total_seconds()),
                int(self.options.critical.total_seconds()))
            )
            cmpt += 1

            msg_err = "Backup is older than {} hours {} minutes " \
                      "(threshold {} : {} hours)"

            # Check threshold
            if self.options.warning:
                if delta_time >= self.options.warning:
                    status = self.warning
                    hours_warn, remains = divmod(
                        int(self.options.warning.total_seconds()), 3600)
                    self.shortoutput = msg_err.format(hours,
                                                      minutes,
                                                      'warn',
                                                      hours_warn)
            if self.options.critical:
                if delta_time >= self.options.critical:
                    status = self.critical
                    hours_crit, remains = divmod(
                        int(self.options.critical.total_seconds()), 3600)
                    self.shortoutput = msg_err.format(hours,
                                                      minutes,
                                                      'crit',
                                                      hours_crit)

        # Return status with message to Nagios
        self.logger.debug("Return status and exit to Nagios.")
        if status:
            status(self.output())
        else:
            self.unknown('Unexpected error during plugin execution, please '
                         'investigate with debug mode on.')
