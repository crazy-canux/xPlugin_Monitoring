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

"""Class definition for XML value trend plugin."""

import logging

from monitoring.nagios.plugin import argument

from .base import PluginBase

import re

logger = logging.getLogger('plugin.trend')


class PluginXMLTrend(PluginBase):
    """Plugin that test the trend of XML interface."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()
        pattern = re.compile(r'/')
        num_tag = 0

       # Get the value of xml_tag
        for obj in xml:
            for key in obj:
                if pattern.split(key.lower())[-1] == self.options.xml_tag:
                    num_tag = num_tag +1
                    self.shortoutput = "OK"
                    self.perfdata.append(
                        '\'{property_name}\'={value}'.format(
                        property_name=key,
                        value=obj[key]))

        if not num_tag:
            status=self.unknown("The tag you specified not exist, please check XML!")
        else:
            status=self.ok

        status(self.output())

    def define_plugin_arguments(self):
        super(PluginXMLTrend, self).define_plugin_arguments()
        self.required_args.add_argument(
            '-t', '--tag',
            dest='xml_tag',
            type=str.lower,
            help='The lowercased string for '
                'the exact tag name in the xml.',
            required=True)

