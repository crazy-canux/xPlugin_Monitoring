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

"""Base class for all Exchange 2010 plugins."""

import logging
import traceback
from monitoring.nagios.plugin import NagiosPluginHTTP

from powershell import XMLTable, XMLSerializedTable
from powershell.xml.exceptions import XMLValidityError


logger = logging.getLogger('plugin.base')


class PluginBase(NagiosPluginHTTP):
    """Base class for all Exchange plugins."""
    def __init__(self, *args, **kwargs):
        super(PluginBase, self).__init__(*args, **kwargs)
        self._alerts = {
            'warning': [],
            'critical': [],
        }
        self.have_criticals = False
        self.have_warnings = False

    def run(self):
        """Run the plugin."""
        try:
            self.main()
        except Exception:
            self.shortoutput = 'Unexpected plugin error ! Please investigate.'
            self.longoutput = traceback.format_exc().splitlines()
            self.unknown(self.output())

    def main(self):
        """Main entry point for the plugin."""
        raise NotImplementedError('Main entry point is not implemented !')

    def fetch_xml_table(self):
        """Helper to fetch the XML via HTTP and parse it."""
        response = self.http.get(self.options.path)

        try:
            xml_table = XMLTable(response.content)
            logger.debug('XML Table: %s', xml_table)
            return xml_table
        except XMLValidityError:
            try:
                xml_table = XMLSerializedTable(response.content)
                logger.debug('XML Serialized Table: %s', xml_table)
                return xml_table
            except XMLValidityError:
                self.shortoutput = 'XML format is not valid !'
                self.longoutput = traceback.format_exc().splitlines()
                self.unknown(self.output())

    def add_critical_result(self, crit_result):
        """
        Add a critical result.

        Used in longoutput to show the result in a CRITICAL section.
        """
        self._alerts['critical'].append(crit_result)
        self.have_criticals = True

    def add_warning_result(self, warn_result):
        """
        Add a warning result.

        Used in longoutput to show the result in a WARNING section.
        """
        self._alerts['warning'].append(warn_result)
        self.have_warnings = True
