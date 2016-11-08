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

"""Class definition for XML decimal plugin."""

import logging

from monitoring.nagios.plugin import argument

from .base import PluginBase

import re

from decimal import Decimal, localcontext

logger = logging.getLogger('plugin.threshold')


class PluginXMLThreshold(PluginBase):
    """Plugin that test the value with decimal."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()
        pattern = re.compile(r'/')

       # Get the value of xml_tag
        for obj in xml:
            for key in obj:
                if pattern.split(key.lower())[-1] == self.options.xml_tag:
                    if obj[key] and not self.options.free:
                        value=Decimal(obj[key])
                        if value >= self.options.critical:
                            self.add_critical_result({key:obj[key]})
                        elif self.options.warning <= value <= self.options.critical:
                            self.add_warning_result({key:obj[key]})
                    elif obj[key] and self.options.free:
                        value=Decimal(obj[key])
                        if value <= self.options.critical:
                            self.add_critical_result({key:obj[key]})
                        elif self.options.critical <= value <= self.options.warning:
                            self.add_warning_result({key:obj[key]})
                    else:
                        self.longoutput.append('\"{property_name}\" value is None' \
                                               ' , please check! '.format(property_name=key) )
       # Exit
        self._prepare_output(problem_pattern='{num} threshold checks with {mol} than '
                            '{thr} ',
                            ok_pattern='All checks seems normal!.')

        if self.have_criticals:
            self.critical(self.output())
        elif self.have_warnings:
            self.warning(self.output())
        else:
            self.ok(self.output())

    def define_plugin_arguments(self):
        super(PluginXMLThreshold, self).define_plugin_arguments()
        self.required_args.add_argument(
            '-t', '--tag',
            dest='xml_tag',
            type=str.lower,
            help='The lowercased string for '
                'the exact tag name in the xml.',
        )

        self.required_args.add_argument(
            '-w', '--warning',
            dest='warning',
            type=float,
            help='Warning threshold for this Plugin.',
            required=False
        )

        self.required_args.add_argument(
            '-c','--critical',
            dest='critical',
            type=float,
            help='Critical threshold for this plugin.',
            required=False
        )

        self.required_args.add_argument(
            '-f', '--free',
            dest='free',
            type=bool,
            help='-f to check the threshold for CPU idle or free disk/mem space!' \
                    ' Use -f yes to enable it. ',
            required=False
        )

    def _prepare_output(self, problem_pattern, ok_pattern):
        """Prepare the message output shown in Nagios."""
        shortoutput = []
        if self.have_criticals or self.have_warnings:
            for severity in sorted(self._alerts.keys()):
                num_alerts = len(self._alerts[severity])
                if num_alerts:
                    if self.options.free:
                        shortoutput.append(
                            problem_pattern.format(num=num_alerts, mol='less',
                                                   thr=getattr(self.options,
                                                               severity)))
                    else:
                        shortoutput.append(
                        problem_pattern.format(num=num_alerts, mol='more',
                                               thr=getattr(self.options,
                                                           severity)))
                self.longoutput.append('====== {} ======'.format(
                    severity.upper()))
                for result in self._alerts[severity]:
                    for key in result:
                        details = '{ItemXPath} , {Value}'.format(
                            ItemXPath=key, Value=result[key])
                    self.longoutput.append(details)
            self.shortoutput = ', '.join(shortoutput)
        else:
            self.shortoutput = ok_pattern
