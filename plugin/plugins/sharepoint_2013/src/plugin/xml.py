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

"""Class definition for XML validity plugin."""

import logging

from datetime import datetime

from monitoring.nagios.plugin import argument

from .base import PluginBase
logger = logging.getLogger('plugin.xml')


class PluginXMLValidity(PluginBase):
    """Plugin that test the validity of XML interface."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()

        # Last modified duration
        xml_age = datetime.now() - xml.last_modified

        # Test timestamp
        if xml_age > self.options.xml_age:
            self.shortoutput = \
                'XML has been last modified ' \
                'since {age} (>= {threshold})!'.format(
                    age=xml.last_modified,
                    threshold=self.options.xml_age)
            status = self.critical
        else:
            self.shortoutput = 'XML is up-to-date.'
            status = self.ok

        # Exit
        status(self.output())

    def define_plugin_arguments(self):
        super(PluginXMLValidity, self).define_plugin_arguments()

        self.required_args.add_argument(
            '--age',
            dest='xml_age',
            type=argument.minutes,
            help='Maximum age of the XML data in minutes.',
            required=True)
