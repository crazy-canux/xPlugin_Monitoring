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


class CheckTSMBackup(BasePlugin):
    """Plugin to check the DB2 TSM backup status."""
    def define_plugin_arguments(self):
        super(CheckTSMBackup, self).define_plugin_arguments()
        self.required_args.add_argument('-b', '--backuptype',
                                        dest="backup_type",
                                        help="Backup type, a char",
                                        required=True)

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
        self.shortoutput = "TSM Backup status is OK."

        now = datetime.now()

        # Final status exit for the plugin
        status = None

        cmd = \
            """echo \"db2 \\"SELECT start_time,end_time,seqnum,location, """ \
            """case """ \
            """when devicetype = 'A' then 'TSM' """ \
            """when devicetype = 'C' then 'Client' """ \
            """when devicetype = 'D' then 'Disk' """ \
            """when devicetype = 'F' then 'Snapshot' """ \
            """when devicetype = 'O' then 'Vendor_device' """ \
            """when devicetype = 'S' then 'Server' """ \
            """when devicetype = 'T' then 'Tape' """ \
            """else 'Unknown' """ \
            """end as OPERATION_TYPE FROM SYSIBMADM.DB_HISTORY """ \
            """WHERE operation='B' and devicetype = '{1}' """ \
            """and sqlcode is null """ \
            """order by seqnum,start_time desc fetch first row only\\"" """ \
            """| sudo -u {0} -i """ \
            """| sed -n '/--/{{n; p;}}' """ \
            """| sed 's/[ ][ ]*/ /g' """ \
            """| sed 's/^\\s*$/NO_DATA/g'""".format(self.options.db2_user,
                                                    self.options.backup_type)

        output = self.run_command(cmd)

        if 'NO_DATA' in output:
            self.critical("No backup has been found ! ")

        # Travel output cmd by line
        cmpt = 0
        for line in output:
            self.logger.debug(line)

            status = self.ok

            try:
                db2_start_time, db2_end_time, db2_seqnum, \
                    db2_location, db2_operation_type = line.split()
            except ValueError as e:
                self.unknown('The number of fields is incorrectly !'
                             '\nException message: {}'.format(e))
            try:
                end_time = datetime.strptime(db2_end_time.strip(),
                                             '%Y%m%d%H%M%S')
            except ValueError as e:
                self.unknown('End datetime is incorrectly formatted !'
                             '\nException message: {}'.format(e))

            try:
                start_time = datetime.strptime(db2_start_time.strip(),
                                               '%Y%m%d%H%M%S')
            except ValueError as e:
                self.unknown('Start datetime is incorrectly formatted !'
                             '\nException message: {}'.format(e))

            self.logger.debug("start_time : {}".format(start_time))

            db2_delta_time = end_time - start_time
            db2_hours, remains = divmod(int(db2_delta_time.total_seconds()),
                                        3600)
            db2_minutes, db2_seconds = divmod(remains, 60)

            self.perfdata.append(
                'backup_duration[{0}]={1}s;;;0;'.format(
                    cmpt, int(db2_delta_time.total_seconds())))

            delta_time = now - end_time
            hours, remains = divmod(int(delta_time.total_seconds()), 3600)
            minutes, remains = divmod(remains, 60)

            self.logger.debug("end_time : {}".format(end_time))

            cmpt += 1

            msg_err = "Backup is older than {} hours {} minutes "
            msg_err += "(threshold {} : {} hours)"

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

            self.longoutput.append(
                "Backup type : {4}, Start Time : {0}, "
                "End Time : {1} \n"
                "Duration : {5} hours {6} minutes {7} seconds \n"
                "Number of Streams : {2}, "
                "Backup Path : {3} ".format(db2_start_time,
                                            db2_end_time,
                                            db2_seqnum,
                                            db2_location,
                                            db2_operation_type,
                                            db2_hours,
                                            db2_minutes,
                                            db2_seconds))

        # Return status with message to Nagios
        self.logger.debug("Return status and exit to Nagios.")
        if status:
            status(self.output())
        else:
            self.unknown('Unexpected error during plugin execution, '
                         'please investigate with debug mode on.')
