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

# Monitoring imports
from monitoring.nagios.plugin import NagiosPluginWMI

import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger('plugin.wmi')


# define new args
class PluginFileAge(NagiosPluginWMI):
    def __init__(self, *args, **kwargs):
        super(PluginFileAge, self).__init__(*args, **kwargs)
        # Convert minute into timedelta format
        self.minute = timedelta(minutes=self.options.minute)
        # Define some vars.
        self.status = None
        self.cmpt = 0

    def define_plugin_arguments(self):
        super(PluginFileAge, self).define_plugin_arguments()
        self.required_args.add_argument('-k', '--drive',
                                        dest='drive',
                                        help='drive',
                                        required=True)
        self.required_args.add_argument('-P', '--path',
                                        dest='path',
                                        help="path",
                                        required=True)
        self.required_args.add_argument('-f', '--filename',
                                        dest='filename',
                                        help="file_name",
                                        required=False)
        self.required_args.add_argument('-m', '--minute',
                                        type=int,
                                        dest="minute",
                                        required=False,
                                        help="the time of the file.")
        self.required_args.add_argument('-e', '--extension',
                                        default='%',
                                        required=False,
                                        help='extension',
                                        dest='extension')

    def get_folder(self, current_date_format, path, filename):
        self.get_file(current_date_format, path, filename)
        # Get all folders.
        folder_data = self.folder_cmd(path)
        if folder_data:
            for folder in folder_data:
                new_path = (folder['Name'].split(":")[1] + "\\").replace(
                    "\\", "\\\\")
                logger.debug("new_path: {}".format(new_path))
                self.get_folder(current_date_format, new_path, filename)

    def get_file(self, current_date_format, path, filename):
        file_data = self.file_cmd(path, filename)
        if file_data:
            self.time_compare(current_date_format, file_data)

    def folder_cmd(self, path):
        cmd_folder = "SELECT FileName FROM CIM_Directory WHERE Drive='{0}' \
            AND Path='{1}'".format(self.options.drive, path)
        logger.debug("cmd_folder: {}".format(cmd_folder))
        folder_data = self.execute(cmd_folder)
        logger.debug("folder_data: {}".format(folder_data))
        return folder_data

    def file_cmd(self, path, filename):
        cmd_file = "SELECT LastModified FROM CIM_DataFile WHERE Drive='{0}' \
        AND Path='{1}' AND FileName LIKE \'{2}\' AND Extension LIKE \'{3}\'".format(
            self.options.drive, path, filename, self.options.extension)
        logger.debug("cmd_file: {}".format(cmd_file))
        file_data = self.execute(cmd_file)
        logger.debug("file_data: {}".format(file_data))
        return file_data

    def time_compare(self, current_date_format, file_data):
        # Compare current_date to all file_data
        # and calculate the outdated file number
        for attribute in file_data:
            if attribute['Name'] and attribute['Name'] != 'Name':
                logger.debug("===== start to compare =====")
                logger.debug("attribute: {}".format(attribute))
                last_mod = datetime.strptime(
                    str(re.split('[.]', attribute['LastModified'])[0]),
                    '%Y%m%d%H%M%S').strftime("%d %B %Y %H:%M:%S")
                last_mod_format = datetime.strptime(last_mod,
                                                    "%d %B %Y %H:%M:%S")
                delta = current_date_format - last_mod_format
                file_name = str(attribute['Name'])

                if delta > self.minute:
                    self.cmpt = self.cmpt + 1
                    if not self.status:
                        self.status = self.critical
                        self.shortoutput = "The file is outdated!"
                    self.longoutput.append(
                        "{0} is outdated - Last update at {1}".format(
                            file_name, last_mod_format))

                # Loggers
                logger.debug("Current Date: {0}".format(current_date_format))
                logger.debug("File last update: {0}".format(last_mod_format))
                logger.debug("File {0} minuts old".format(delta))
                logger.debug("Compare with : {0}".format(self.minute))

        if self.cmpt == 0:
            self.status = self.ok
            self.shortoutput = "All files are updated!"


def main():
    # Init plugin
    plugin = PluginFileAge(version="2.0.0", description="check age of files")

    # System time.
    cmd_time = "SELECT LocalDateTime FROM Win32_OperatingSystem"
    logger.debug("cmd_time: {}".format(cmd_time))
    remote_hour = plugin.execute(cmd_time)
    logger.debug("time_data: {}".format(remote_hour))
    if not remote_hour:
        plugin.unknown("Get LocalDateTime error, output empty.")

    # Attrs to remote_hour
    for attribute in remote_hour:
        current_date = datetime.strptime(
            str(re.split('[.]', attribute['LocalDateTime'])[0]),
            '%Y%m%d%H%M%S').strftime("%d %B %Y %H:%M:%S")
        # '19 October 2015 05:33:10'
        current_date_format = datetime.strptime(current_date,
                                                "%d %B %Y %H:%M:%S")

    # Get the filename.
    if plugin.options.filename:
        plugin.get_file(current_date_format,
                        plugin.options.path,
                        plugin.options.filename)
    else:
        filename = "%"
        plugin.get_folder(current_date_format,
                          plugin.options.path, filename)

    # Return status with message to Nagios
    logger.debug("Return status and exit to Nagios.")
    if plugin.status:
        plugin.status(plugin.output())
    else:
        plugin.unknown('Unexpected error during plugin execution,\
                       please investigate with debug mode on.')

if __name__ == "__main__":
    main()
