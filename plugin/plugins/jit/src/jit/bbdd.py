# -*- coding: utf-8 -*-
# Copyright (C) Faurecia <http://www.faurecia.com/>
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

from monitoring.nagios.plugin import NagiosPluginMSSQL


class BBDDCheck(NagiosPluginMSSQL):
    """
    This class represent BBDD type check.
    """

    def define_plugin_arguments(self):
        """
        Define arguments for the plugin.
        """
        super(BBDDCheck, self).define_plugin_arguments()

        self._parser_thresholds_group = self.parser.add_argument_group(
            "Thresholds", "Options for thresholds.")
        self._parser_thresholds_group.add_argument(
            '-w',
            type=int,
            dest='warning',
            help='Warning threshold in MBytes of used space.')

        self._parser_thresholds_group.add_argument(
            '-c',
            type=int,
            dest='critical',
            help='Critical threshold in MBytes of used space.')

        self.required_args.add_argument(
            '-f',
            dest='dbfile',
            choices=['rows', 'log'],
            default='rows',
            help="Type of the database file to check. Either 'rows' or 'log'. "
                 "Default 'rows'.",
            required=True)

    def verify_plugin_arguments(self):
        """
        Do sanity checks on arguments provided from command line.
        """
        super(BBDDCheck, self).verify_plugin_arguments()

        if (self.options.warning and not self.options.critical) or \
           (not self.options.warning and self.options.critical):
            self.unknown('You must specify all thresholds !')

        if self.options.warning and not self.options.warning > 0:
            self.unknown('Warning threshold must be > 0 !')

        if self.options.critical and not self.options.critical > 0:
            self.unknown('Critical threshold must be > 0 !')

        if self.options.warning and self.options.critical:
            if self.options.warning >= self.options.critical:
                self.unknown('Warning threshold cannot be higher than '
                             'critical !')
