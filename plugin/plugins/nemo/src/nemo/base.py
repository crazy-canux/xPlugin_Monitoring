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

import re
import bs4
import requests
import logging

from monitoring.nagios.plugin import NagiosPlugin
from monitoring.nagios.exceptions import NagiosUnknown


logger = logging.getLogger('plugin.nemo.base')


class NemoPlugin(NagiosPlugin):
    """
    Download and fetch XML file

    Args :
        url - URL to fetch Nemo XML
    """

    #Default XML path
    xml_urls = [
        'http://wwgrpctm0001.ww.corp:8181/nemo.xml',
        'http://wwgrpctm0002.ww.corp:8181/nemo.xml',
        'http://wwgrpctm0003.ww.corp:8181/nemo.xml',
        'http://wwgrpctm0004.ww.corp:8181/nemo.xml',
    ]

    #Attrs
    job_queue = re.compile(r'^nemo_.*')

    def define_plugin_arguments(self):
        super(NemoPlugin, self).define_plugin_arguments()

        self.required_args.add_argument('--url',
                                        dest="url",
                                        action='append',
                                        help="(Optional) Redefine URL to fetch "
                                             "Nemo XML",
                                        required=False)

    def initialize(self):
        super(NemoPlugin, self).initialize()

        self.options.hostname = self.options.hostname.lower()

        # Select URL to use (given by user or by default)
        if self.options.url:
            urls = self.options.url
        else:
            urls = NemoPlugin.xml_urls

        # Get the XML content
        logger.debug('Fetching XML file using \'%s\'...', ", ".join(urls))
        try:
            for url in urls:
                r = requests.get(url)
                if r.status_code == requests.codes.ok:
                    self.xml = bs4.BeautifulSoup(r.text)
                    break

            if not hasattr(self, 'xml'):
                raise NagiosUnknown('No XML content '
                                    'delivered by URLs: %s' % ", ".join(urls))
        except Exception as e:
            self.unknown('Error: %s' % e)
