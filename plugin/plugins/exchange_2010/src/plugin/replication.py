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

"""Class definition for Replication health plugins."""

import logging

from .base import PluginBase

logger = logging.getLogger('plugin.replication')


class PluginXMLReplication(PluginBase):
    """Plugin class for Replication health plugin."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()
        fails = xml.match(object_name='ReplicationCheckOutcome',
                          property_name='Result',
                          regex='^Passed$',
                          invert=True)

        if fails:
            logger.debug("Failed replicaton checks IDs: %s",
                         ', '.join([fail.refid for fail in fails]))
            self.shortoutput = 'There are {num} replication ' \
                               'errors !'.format(num=len(fails))
            for entry in fails:
                self.longoutput.append(
                    '[{Result}] Check: "{Check}" '
                    '-- **{Error}**'.format(**entry))
            status = self.critical
        else:
            self.shortoutput = 'Replication health is normal.'
            status = self.ok

        # Exit
        status(self.output())
