#!/usr/bin/env python2.7
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

"""
This plugin check AD 2012 application using a XML interface.
"""

from __future__ import division

import logging
import operator
import argparse
import re
import traceback

from decimal import Decimal, localcontext

from monitoring.nagios.plugin import NagiosPluginHTTP, argument

logger = logging.getLogger('plugin')


# Define new args
class PluginAd2012(NagiosPluginHTTP):
    """Customize plugin behavior."""

    def __init__(self, *args, **kwargs):
        super(PluginAd2012, self).__init__(*args, **kwargs)

        try:
            self.__http_response = self.http.get(self.options.path)
            self.__xml = self.__http_response.xml()
            self.status = None
            self.server_tag = self.__xml.find_all('server')[0]
            self.shortoutput_pattern = '{label}: {value} {unit} {threshold}'
            self.shortoutput_vars = {
                'label': self.options.label,
                'unit': self.options.unit,
                'threshold': '',
            }
        except Exception:
            self.shortoutput = "Something unexpected happend " \
                "when init the class. Please investigate..."
            self.longoutput = traceback.format_exc().splitlines()
            self.unknown(self.output())

    def define_plugin_arguments(self):
        super(PluginAd2012, self).define_plugin_arguments()

        # Common arguments
        common_arguments = argparse.ArgumentParser(add_help=False)
        common_arguments.add_argument('-u', '--unit',
                                      dest='unit',
                                      help='Unit used in graphs '
                                           'or in plugin output.',
                                      default='')
        common_arguments.add_argument('-l', '--label',
                                      dest='label',
                                      help='For the value in plugin output '
                                           'or graph data source.',
                                      required=True)
        common_arguments.add_argument('--no_perfdata',
                                      action='store_true',
                                      help='Disable performance data.',
                                      required=False)
        common_arguments.add_argument('-t', '--tag',
                                      dest='tag',
                                      type=str.lower,
                                      help='The lowercased string for '
                                           'the exact tag name in the XML.',
                                      required=True)

        # Check Modes
        # ===========
        #
        checkmodes = self.parser.add_subparsers(
            title='Mode',
            description='Behavior of the plugin',
            help="Select check mode for the plugin. See --help for that "
                 "command for details.",
            dest="mode")

        # Decimal
        mode_decimal = checkmodes.add_parser(
            'decimal',
            description='Fetch and handle decimal value types.',
            parents=[common_arguments])
        mode_decimal.add_argument('-w', '--warning',
                                  dest='warning',
                                  type=argument.NagiosThreshold)
        mode_decimal.add_argument('-c', '--critical',
                                  dest='critical',
                                  type=argument.NagiosThreshold)

        # DNS
        mode_dns = checkmodes.add_parser(
            'dns',
            description='Fetch the DNS test status.',
            parents=[common_arguments])
        mode_dns.add_argument('-r', '--regexp',
                              dest='regexp',
                              type=re.compile,
                              help='Pattern that match the DNS status. This '
                                   'is a regular expression.',
                              required=True)

        # Memory usage
        mode_memory = checkmodes.add_parser(
            'memory',
            description='Compute used memory from fetched value.',
            parents=[common_arguments])
        mode_memory.add_argument('-w', '--warning',
                                 dest='warning',
                                 type=argument.NagiosThreshold)
        mode_memory.add_argument('-c', '--critical',
                                 dest='critical',
                                 type=argument.NagiosThreshold)

        # Empty tag
        checkmodes.add_parser(
            'session',
            description='Use this mode to detect if there are logon sessions.',
            parents=[common_arguments])

    def checkmode_decimal(self):
        """
        Fetch a tag value as a decimal and compare against thresholds.
        """
        with localcontext() as ctx:
            ctx.prec = 3

            try:
                value = Decimal(self.get_tag_content(self.options.tag))
            except Exception:
                self.shortoutput = "Something unexpected happend in " \
                    "checkmode_decimal. Please investigate..."
                self.longoutput = traceback.format_exc().splitlines()
                self.unknown(self.output())

        self.shortoutput_vars['value'] = value
        self.test_and_exit(value)

    def checkmode_memory(self):
        """
        Compute the used memory of the given value against the server total
        memory.
        """
        with localcontext() as ctx:
            # Use a context precision of 3 for all decimal operations
            ctx.prec = 3
            try:
                mem_used = Decimal(self.get_tag_content(self.options.tag)) / \
                    1024
                total_physical_memory = Decimal(
                    self.get_tag_content('totalvisiblememorysize'))
                used_mem_percent = Decimal(
                    (mem_used / total_physical_memory) * 100)
            except Exception:
                self.shortoutput = "Something unexpected happend in " \
                    "checkmode_decimal. Please investigate..."
                self.longoutput = traceback.format_exc().splitlines()
                self.unknown(self.output())

        self.shortoutput_vars['value'] = used_mem_percent

        self.test_and_exit(used_mem_percent)

    def checkmode_session(self):
        """
        Test there are logon sessions.
        """

        tag_content = self.get_tag_content(self.options.tag)
        self.shortoutput_pattern = '{message}'
        self.shortoutput_vars = {
            'message': ''
        }
        self.status = self.ok

        if "No Connection" in tag_content:
            self.shortoutput_vars['message'] = "No active logon session."
        else:
            self.shortoutput_vars['message'] = "Active logon sessions found."
            self.longoutput.append(tag_content)

        self.terminate()

    def checkmode_dns(self):
        """
        Fetch DNS status in XML.
        """
        value = self.get_tag_content(self.options.tag)
        value = value.strip('\n')
        self.shortoutput_vars['value'] = value
        self.test_regexp_and_exit(self.options.regexp, value)

    def get_tag_content(self, tag):
        """
        Get the content of a tag from the XML.

        :param tag: the tag name as a dotted notation for children.
        :returns: the content of a tag as a string.
        """
        attrgetter = operator.attrgetter(tag)

        try:
            tag_data = attrgetter(self.server_tag).text
            if not isinstance(tag_data, basestring) or not len(tag_data):
                raise AttributeError('The tag data is empty !')

            logger.debug('Tag: {0}'.format(tag))
            logger.debug('Tag Raw Data: {0}'.format(tag_data))

            return tag_data
        except AttributeError as e:
            self.shortoutput = 'Cannot determinate {0} value !'.format(tag)
            self.longoutput = [str(e)]
            self.unknown(self.output())

    def test_and_exit(self, value):
        """
        Test ``value`` against standard Nagios thresholds and exit with status
        to Nagios.

        :param value: a decimal value to test.
        :type value: decimal
        """
        # Compare with the given thresholds and give the Nagios satus
        if self.options.critical is not None \
           and self.options.critical.test(value):
            self.status = self.critical
            self.shortoutput_vars['threshold'] = "({})".format(
                self.options.critical)
        elif self.options.warning is not None \
                and self.options.warning.test(value):
            self.status = self.warning
            self.shortoutput_vars['threshold'] = "({})".format(
                self.options.warning)
        else:
            self.status = self.ok

        # Add performance data
        if not self.options.no_perfdata:
            self.perfdata.append(
                "'{0}'={1}{2};;;0;".format(self.options.label,
                                           value,
                                           self.options.unit))

        # Done
        self.terminate()

    def test_regexp_and_exit(self, regexp, value):
        """
        Test on ``regexp`` and ``value``. Returns status to Nagios.
        """
        if regexp.match(value):
            self.status = self.critical
        else:
            self.status = self.ok
        # Done
        self.terminate()

    def terminate(self):
        """Terminate the plugin execution and give result to Nagios."""
        if self.status:
            # Format output
            self.shortoutput = self.shortoutput_pattern.format(
                **self.shortoutput_vars)
            self.status(self.output())
        else:
            self.unknown('Unexpected error during plugin execution, please '
                         'investigate with debug mode on.')

plugin = PluginAd2012(version='1.1.0', description='Checks for AD 2012.')

# Run the right check mode
try:
    run = getattr(plugin, 'checkmode_{}'.format(plugin.options.mode))
except AttributeError:
    plugin.unknown('The check mode "{0}" is not yet implemented !\n'
                   'The method checkmode_{0}() cannot be found within the '
                   'plugin class.'.format(plugin.options.mode))
else:
    run()
