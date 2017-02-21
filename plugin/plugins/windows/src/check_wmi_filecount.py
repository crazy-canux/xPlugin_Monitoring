#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
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

# Monitoring imports
from monitoring.nagios.plugin import NagiosPluginWMI

import logging

logger = logging.getLogger('plugin.wmi')


# define new args
class PluginFileCount(NagiosPluginWMI):
    def __init__(self, *args, **kwargs):
        super(PluginFileCount, self).__init__(*args, **kwargs)
        self.count = 0

    def define_plugin_arguments(self):
        super(PluginFileCount, self).define_plugin_arguments()
        self.required_args.add_argument("-m", "--multi",
                                        dest="multi",
                                        action="store_true",
                                        help="check the sub folder.")
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
        self.required_args.add_argument('-w', '--warning',
                                        dest="warning",
                                        type=int,
                                        default=0,
                                        required=False,
                                        help="the warning of the file number.")
        self.required_args.add_argument('-c', '--critical',
                                        dest="critical",
                                        type=int,
                                        default=0,
                                        required=False,
                                        help="the critical of the file number")

    def get_folder(self, path, filename):
        num = self.get_file(path, filename)
        self.count += num
        # Get all folders.
        folder_data = self.folder_cmd(path)
        if folder_data:
            for folder in folder_data:
                new_path = (folder['Name'].split(":")[1] + "\\").replace(
                    "\\", "\\\\")
                logger.debug("new_path: {}".format(new_path))
                self.get_folder(new_path, filename)
        return self.count

    def get_file(self, path, filename):
        file_data = self.file_cmd(path, filename)
        if file_data:
            num = len(file_data)
            logger.debug("num: {}".format(num))
            return num
        else:
            return 0

    def folder_cmd(self, path):
        cmd_folder = "SELECT FileName FROM CIM_Directory WHERE Drive='{0}' \
            AND Path='{1}'".format(self.options.drive, path)
        logger.debug("cmd_folder: {}".format(cmd_folder))
        folder_data = self.execute(cmd_folder)
        logger.debug("folder_data: {}".format(folder_data))
        return folder_data

    def file_cmd(self, path, filename):
        cmd_file = "SELECT Name FROM CIM_DataFile WHERE Drive='{0}' AND \
            Path='{1}' AND FileName LIKE \"{2}\"".format(self.options.drive,
                                                         path, filename)
        logger.debug("cmd_file: {}".format(cmd_file))
        file_data = self.execute(cmd_file)
        logger.debug("file_data: {}".format(file_data))
        return file_data


def main():
    # Init the status.
    status = None

    # Init plugin
    plugin = PluginFileCount(version="1.0.0", description="get number of file")

    # get the file number.
    if plugin.options.multi:
        count = plugin.get_folder(plugin.options.path, plugin.options.filename)

    else:
        count = plugin.get_file(plugin.options.path, plugin.options.filename)

    if not count:
        count = 0
    status = plugin.ok

    # Compare the number.
    if plugin.options.warning:
        if count > plugin.options.warning:
            status = plugin.warning
    if plugin.options.critical:
        if count > plugin.options.critical:
            status = plugin.critical

    plugin.shortoutput = "The number of the file in {0}{1} is {2}".format(
        plugin.options.drive, plugin.options.path, count)
    plugin.perfdata.append("count={result};{warn};{crit};0;".format(
        crit=plugin.options.critical,
        warn=plugin.options.warning,
        result=count))

    # Return status with message to Nagios
    logger.debug("Return status and exit to Nagios.")
    if status:
        status(plugin.output())
    else:
        plugin.unknown('Unexpected error during plugin execution,\
                       please investigate with debug mode on.')

if __name__ == "__main__":
    main()
