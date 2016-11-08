# -*- coding: utf-8 -*-
# Copyright (c) Canux <http://www.Company.com/>
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
from time import time, mktime

from .base import BasePlugin


class CheckVTLBackup(BasePlugin):
    """Plugin to check the DB2 TSM VTL backup status."""
    def define_plugin_arguments(self):
        super(CheckVTLBackup, self).define_plugin_arguments()
        self.required_args.add_argument('-w', '--warn',
                                        type=int,
                                        dest='warning',
                                        default=86400,
                                        help="Warning threshold. "
                                             "Default value is 86400(24H).",
                                        required=False)

        self.required_args.add_argument('-c', '--crit',
                                        type=int,
                                        dest='critical',
                                        default=86400,
                                        help='Critical threshold.'
                                             'Default value is 86400(24H).',
                                        required=False)

    def main(self):
        """Main plugin execution."""

        # Final status exit for the plugin
        status = None

        # Get the current seconds of time.
        now_time = datetime.now().strftime("%Y%m%d%H%M%S")
        now_sec = time()
        self.logger.debug("now_time: {}".format(now_time))
        self.logger.debug("now_sec: {}".format(now_sec))

        cmd = \
            """echo $(echo""" \
            """ "./sqllib/acs/fcmcli -f inquire_detail" """ \
            """| sudo -u {0} -i""" \
            """| grep BACKUP""" \
            """| tr "\\n" "\\%" """ \
            """| sed -e "s/\%\#/\\\\\\n\#/g" -e "s/ *\% */ /g")""" \
            """| grep -E "TAPE_BACKUP_COMPLETE|TAPE_BACKUP_FAILED" """.format(
                self.options.db2_user)
        self.logger.debug("cmd: {0}".format(cmd))

        try:
            output = self.run_command(cmd)
        except ValueError as e:
            self.unknown('The command is error!'
                         '\nException message: {}'.format(e))

        self.logger.debug("output: {}".format(output))

        # To check if there is a backup failed.
        tag = 0
        if "TAPE_BACKUP_FAILED" in "".join(output):
            tag = 1

        # Get the first line as the new new one.
        temp_time = "".join(output).split()[2]
        temp_time_sec = mktime(datetime.timetuple(
            datetime.strptime(temp_time, '%Y%m%d%H%M%S')))
        temp_sec = now_sec - temp_time_sec

        for line in output:
            self.logger.debug("line: {}".format(line))

            try:
                warn_time = line.split()[2]
                crit_time = line.split()[3]
                targetset = line.split()[6]
                self.logger.debug("warn_time: {}".format(warn_time))
                self.logger.debug("crit_time: {}".format(crit_time))
                self.logger.debug("targetset: {}".format(targetset))

            except ValueError as e:
                self.unknown('The warning and critical time is wrong!'
                             '\nException message: {}'.format(e))

            # If there is a backup failed, the result is critical.
            if "TAPE_BACKUP_FAILED" in line:
                name = "TAPE_BACKUP_FAILED"
                status = self.critical
                self.shortoutput = "TSM VTL Backup status is critical."

            elif "TAPE_BACKUP_COMPLETE" in line:
                name = "TAPE_BACKUP_COMPLETE"
                # If there is a backup failed, the result is critical.
                if tag:
                    status = self.critical
                    self.shortoutput = "TSM VTL Backup status is critical."
                # If there is no backup failed, then compare the time.
                else:
                    status = self.ok
                    self.shortoutput = "TSM VTL Backup status is OK."
                    try:
                        warn_time_sec = mktime(datetime.timetuple(
                            datetime.strptime(warn_time, '%Y%m%d%H%M%S')))
                        crit_time_sec = mktime(datetime.timetuple(
                            datetime.strptime(crit_time, '%Y%m%d%H%M%S')))
                        self.logger.debug("warn_time_sec:{}".format(
                            warn_time_sec))
                        self.logger.debug("crit_time_sec:{}".format(
                            crit_time_sec))

                        warn_sec = now_sec - warn_time_sec
                        crit_sec = now_sec - crit_time_sec
                        self.logger.debug("warn_sec: {}".format(warn_sec))
                        self.logger.debug("crit_sec: {}".format(crit_sec))

                        if warn_sec <= temp_sec:
                            temp_sec = warn_sec
                            self.logger.debug("temp_sec: {}".format(temp_sec))

                            # Check threshold
                            if self.options.warning:
                                if warn_sec >= self.options.warning:
                                    status = self.warning
                                    self.shortoutput = "TSM VTL Backup status \
                                        is warning."

                            if self.options.critical:
                                if crit_sec >= self.options.critical:
                                    status = self.critical
                                    self.shortoutput = "TSM VTL Backup status \
                                        is critical."

                    except ValueError as e:
                        self.unknown('The warning and critical value is wrong!'
                                     '\nException message: {}'.format(e))

            self.longoutput.append(
                "{0}: Consistency group {1},"
                "snapshot: {2}, offload: {3}".format(name,
                                                     targetset,
                                                     warn_time,
                                                     crit_time))

        # Return status with message to Nagios
        self.logger.debug("Return status and exit to Nagios.")
        if status:
            status(self.output())
        else:
            self.unknown('Unexpected error during plugin execution, '
                         'please investigate with debug mode on.')
