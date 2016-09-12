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

import logging
import datetime
from urllib2 import urlopen, HTTPError

from monitoring.nagios.plugin import NagiosPlugin


logger = logging.getLogger("plugin.exalead.base")


class ExaleadBase(NagiosPlugin):
    """
    Class for an Exalead Plugin
    """
    def initialize(self):
        """Plugin initialization"""
        super(ExaleadBase, self).initialize()

        # Plugin attributes
        self.xml_namespaces = {
            'buildgroup': '{exa:com.exalead.mercury.mami.indexing.v10}',
            'deployment': '{exa:exa.bee.deploy.v10}',
        }
        self.port = self.options.baseport + 11
        self.host = self.options.hostname
        self.url = ''

    def define_plugin_arguments(self):
        """Define specific plugin arguments"""
        super(ExaleadBase, self).define_plugin_arguments()

        self.required_args.add_argument('-p', '--baseport',
                                        type=int,
                                        dest='baseport',
                                        default='10000',
                                        help='Base port of Exalead instance')

    def getXMLData(self):
        logger.debug('Get XML data:')
        logger.debug("\tURL: {0}".format(self.url))
        try:
            url = urlopen(self.url)
        except HTTPError as error:
            raise self.unknown('Error fetching URL: {0}'.format(error))
        return url

    def calc_commit_age(self, last_commit):
        today = datetime.datetime.now()
        delta = today - last_commit

        logger.debug('Today date: {0}'.format(today))
        logger.debug(
            'Delta between last commit date and threshold: {0}'.format(delta))
        return delta