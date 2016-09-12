#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#===============================================================================
# Filename      : check_ssh_file_existence
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Check on remote server if some files are present using SSH.
#-------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================

__version__ = '0.2.4'

import hashlib
import logging as log
from pprint import pformat
import re
from datetime import datetime, timedelta

from monitoring.nagios.plugin import NagiosPluginSSH

logger = log.getLogger('plugin')

def format_time_from_arg(time_string):
    """
    Format a time string from args and return a datetime.

    :param time_string: String of the form HH:MM:SS.
    :type time_string: str
    :return: datetime
    """
    time_from_arg = datetime.strptime(time_string, '%H:%M:%S')
    current_time = datetime.today()
    check_time = time_from_arg.replace(year=current_time.year, month=current_time.month, day=current_time.day)
    return check_time


class PluginCheckFileExistence(NagiosPluginSSH):
    """
    Plugin customization class.
    """

    def initialize(self):
        super(PluginCheckFileExistence, self).initialize()

        # Use MD5 hash in pickle file name for the case you have multiple service check on the same host that use
        # this plugin.
        pickle_pattern = '%s_%s_%s' % (self.options.hostname, self.options.regexp.pattern, self.options.directory)
        self.picklefile_pattern = hashlib.md5(pickle_pattern).hexdigest()

        self.has_check_period = False
        self.in_check_period = False
        self.flags = {
            'DoneForToday': False,
            'NotYetPresent': None,
            'Files': [],
        }

    def define_plugin_arguments(self):
        super(PluginCheckFileExistence, self).define_plugin_arguments()

        parser_file_group = self.parser.add_argument_group('Files', 'Arguments to list and filter files.')
        parser_file_group.add_argument('-d',
                                        dest='directory',
                                        default='.',
                                        help='Directory to look files in. Default to the current directory.')
        parser_file_group.add_argument('-r',
                                        dest='regexp',
                                        default=re.compile(r'.*'),
                                        type=re.compile,
                                        help='Regexp pattern to filter files. Default to all \'.*\'.')
        parser_file_group.add_argument('-n',
                                       dest='count',
                                       type=int,
                                       default=1,
                                       help='Number of file (at least) that must be found to consider it is valid. ' \
                                            'Default to 1 occurence.')
        parser_file_group.add_argument('--stime',
                                       dest='stime',
                                       type=format_time_from_arg,
                                       help='Check start time. Check for files starting at the specified time.')
        parser_file_group.add_argument('--etime',
                                       dest='etime',
                                       type=format_time_from_arg,
                                       help='Check end time. Do not check for files above this time.')

    def verify_plugin_arguments(self):
        super(PluginCheckFileExistence, self).verify_plugin_arguments()

        # Check time thresholds syntax
        if self.options.stime and self.options.etime:
            if self.options.stime >= self.options.etime:
                self.unknown('Start time cannot be >= end time, check syntax !')

            if datetime.today() > self.options.etime:
                tomorrow = timedelta(days=1)
                self.options.stime += tomorrow
                self.options.etime += tomorrow

            logger.debug('We must take care of the time period.')
            logger.debug('\tStart time: %s' % self.options.stime)
            logger.debug('\tEnd time: %s' % self.options.etime)

            self.has_check_period = True

            if (datetime.today() > self.options.stime) and (datetime.today() < self.options.etime):
                logger.debug('We are in check period...')
                self.in_check_period = True
            else:
                logger.debug('We are not in check period...')
        elif (self.options.stime and not self.options.etime) or (not self.options.stime and self.options.etime):
            self.unknown('Missing start/end time information, check syntax !')

    def search_files(self, files):
        found = []
        regexp = self.options.regexp
        for file in files:
            if regexp.search(file):
                logger.debug('\tFound file \'%s\'.' % file)
                found.append(file)
        return found


plugin = PluginCheckFileExistence(description='Check on remote server if some files are present using SSH.',
                         version=__version__)

# Look for files on the remote server.
files = plugin.ssh.list_files(plugin.options.directory)
logger.debug('Retrieve files list:')
logger.debug(pformat(files))

# Search files using the regexp
found_files = plugin.search_files(files)

# Should we check if plugin must be executed ?
status = None
message = ''
if plugin.has_check_period:
    # Check period defined

    # Load previous state
    try:
        flags = plugin.load_data()
    except IOError:
        flags = plugin.flags

    if plugin.in_check_period:
        if flags['DoneForToday']:
            status = plugin.ok
            message =   '%d files have already been checked today.\n'\
                        'The following files have been found:\n'\
                        '%s' % (len(flags['Files']), '\n'.join(flags['Files']))
        else:
            if found_files:
                if len(found_files) >= plugin.options.count:
                    flags['Files'] = found_files
                    flags['DoneForToday'] = True
                    flags['NotYetPresent'] = None
                    status = plugin.ok
                    message =   '%d files with regexp \"%s\" have been found in \"%s\".\n'\
                                'The following files have been found:\n'\
                                '%s' % (len(found_files),
                                        plugin.options.regexp.pattern,
                                        plugin.options.directory,
                                        '\n'.join(found_files))
                else:
                    status = plugin.critical
                    message = 'Only %d files with regexp \"%s\" have been found in \"%s\".'\
                              'Should be at least %d.\n' % (len(found_files),
                                                            plugin.options.regexp.pattern,
                                                            plugin.options.directory,
                                                            plugin.options.count)
            else:
                flags['NotYetPresent'] = True
                status = plugin.ok
                message =   'Files with regexp \"%s\" are not yet present in \"%s\".'\
                            'Verify in next check...' % (plugin.options.regexp.pattern, plugin.options.directory)
    else:
        if flags['NotYetPresent']:
            status = plugin.critical
            message = 'Files have not been received today !'
        else:
            # Compute the start time
            start = int((plugin.options.stime - datetime.today()).total_seconds())
            hours, remainder = divmod(start, 3600)
            minutes, seconds = divmod(remainder, 60)

            flags['DoneForToday'] = False
            status = plugin.ok
            message = 'Nothing to do. Will start to do something in %s hours, %s mins and %s secs.' % (hours,
                                                                                                       minutes,
                                                                                                       seconds)

    logger.debug('Flags status:')
    logger.debug(pformat(flags, indent=4))

    plugin.save_data(flags)
else:
    # No check period, run all the time
    if found_files:
        if len(found_files) >= plugin.options.count:
            status = plugin.ok
            message =   '%d files with regexp \"%s\" have been found in \"%s\".\n'\
                        'The following files have been found:\n'\
                        '%s' % (len(found_files),
                                plugin.options.regexp.pattern,
                                plugin.options.directory,
                                '\n'.join(found_files))
        else:
            status = plugin.critical
            message = 'Only %d files with regexp \"%s\" have been found in \"%s\".'\
                      'Should be at least %d.\n' % (len(found_files),
                                                    plugin.options.regexp.pattern,
                                                    plugin.options.directory,
                                                    plugin.options.count)
    else:
        status = plugin.critical
        message = 'Cannot find files with regexp \"%s\" in \"%s\" !' % (plugin.options.regexp.pattern,
                                                                        plugin.options.directory)

# Return status to Nagios
status(message)
