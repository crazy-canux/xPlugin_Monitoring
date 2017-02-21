# -*- coding: utf-8 -*-
# Copyright (c) 2015 Canux CHENG <canuxcheng@gmail.com>
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

from .base import BasePlugin


class CheckDatabaseLog(BasePlugin):
    """Plugin to check the DB2 database log state."""
    def define_plugin_arguments(self):
        super(CheckDatabaseLog, self).define_plugin_arguments()
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

    def main(self):
        """Main plugin execution."""
        # Final status exit for the plugin
        status = None

        # Returns 3 fields:
        # "log used %" "Total log used/MB" "Total log available/MB"
        cmd = \
            """echo "db2 \\"SELECT CASE (TOTAL_LOG_AVAILABLE) """\
            """WHEN -1 THEN DEC(-1,5,2) """\
            """ELSE DEC(100 * (FLOAT(TOTAL_LOG_USED)/""" \
            """FLOAT(TOTAL_LOG_USED + TOTAL_LOG_AVAILABLE)), 5,2) END, """\
            """TOTAL_LOG_USED / 1024/1024, """ \
            """CASE (TOTAL_LOG_AVAILABLE) """ \
            """WHEN -1 THEN -1 """ \
            """ELSE TOTAL_LOG_AVAILABLE / 1024/1024 END """ \
            """FROM SYSIBMADM.SNAPDB \\"" """ \
            """| sudo -u {0} -i """ \
            """| sed -n '/--/{{n; p;}}' """ \
            """| sed 's/[ ][ ]*/ /g'""".format(self.options.db2_user)

        output = self.run_command(cmd)

        # Travel output cmd by line
        cmpt = 0
        for line in output:
            self.logger.debug("line : {0}".format(line))

            status = self.ok
            log_use, total_log_use, total_log_available = line.split()
            log_used = float(log_use)

            self.shortoutput = "Database Log Used {} % ( {} / {} MB)".format(
                log_used, total_log_use, total_log_available)
            self.perfdata.append('log_used[{0}]={1}%;{2};{3};0;'.format(
                cmpt, log_used, self.options.warning, self.options.critical))

            cmpt += 1

            # Check threshold
            if self.options.warning:
                if log_used >= self.options.warning:
                    status = self.warning
            if self.options.critical:
                if log_used >= self.options.critical:
                    status = self.critical

        # Return status with message to Nagios
        self.logger.debug("Return status and exit to Nagios.")
        if status:
            status(self.output())
        else:
            self.unknown('Unexpected error during plugin execution, '
                         'please investigate with debug mode on.')
