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

"""Class definition for application pool status plugin."""

import logging
import re

from .base import PluginBase

logger = logging.getLogger('plugin.pool')


class PluginXMLPool(PluginBase):
    """Plugin class for pool status of sharepoint plugin."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()

        apppool_name_pattern = re.compile(r".*@name='(.*)'.*")
        status_pattern = re.compile(r'Stopped')

        fails = []
        oks = []
        for result in xml:
            for key in result:
                apppool_name = apppool_name_pattern.match(key)
                if apppool_name:
                    pool_name = apppool_name.group(1)
                else:
                    pool_name = key

                if self.options.list_apppool:
                    lists = self.options.list_apppool.split(',')
                    if pool_name not in lists:
                        continue

                if status_pattern.match(result[key]):
                    fails.append(pool_name)
                else:
                    oks.append(pool_name)

        if fails:
            self.shortoutput = 'There are {num} pool ' \
                               'Stopped !'.format(num=len(fails))
            self.longoutput.append(' --- {num} Pool : STOPPED ---'
                                   .format(num=len(fails)))
            for entry in fails:
                self.longoutput.append('Pool Name: "{}" '.format(entry))
            self.longoutput.append('')
            status = self.critical
        else:
            if oks:
                self.shortoutput = 'All pools started.'
                status = self.ok
            else:
                self.shortoutput = 'No pool found'
                status = self.unknown

        if oks:
            self.longoutput.append(' --- {num} Pool : Started ---'
                                   .format(num=len(oks)))
            for entry in oks:
                self.longoutput.append('Pool Name: "{}" '.format(entry))
        # Exit
        status(self.output())

    def define_plugin_arguments(self):
        """Extra plugin arguments."""
        super(PluginXMLPool, self).define_plugin_arguments()
        self.required_args.add_argument('-l',
                                        dest='list_apppool',
                                        help='Application pool name (comma '
                                             'separated).')
