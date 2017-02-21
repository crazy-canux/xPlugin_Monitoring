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

"""Class definition for CAS server plugins."""

import logging

from .base import PluginBase

logger = logging.getLogger('plugin.cas')


class PluginXMLCAS(PluginBase):
    """Plugin class for CAS plugin."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()
        fails = xml.match('Result', '^Success$', invert=True)

        if fails:
            self.shortoutput = 'There are {num} failed ' \
                               'scenarios !'.format(num=len(fails))
            for entry in fails:
                self.longoutput.append(
                    '[{Result}] Scenario: "{Scenario}" '
                    '-- **{Error}**'.format(**entry))
            status = self.critical
        else:
            self.shortoutput = 'All scenarios have successfully passed.'
            for entry in xml:
                self.longoutput.append(
                    '[{Result}] Scenario: "{Scenario}"'.format(**entry))
            status = self.ok

        # Exit
        status(self.output())
