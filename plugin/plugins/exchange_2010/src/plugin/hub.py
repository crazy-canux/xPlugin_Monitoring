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

"""Class definition for HUB transport server plugins."""

import logging

from .base import PluginBase

logger = logging.getLogger('plugin.hub')


class PluginXMLHUB(PluginBase):
    """Plugin class for HUB transport server plugin."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()
        failed_status = xml.match(property_name='Status',
                                  regex='^(Ready|Active|Connecting)$',
                                  invert=True)

        # Failed statuses
        if failed_status:
            self.have_criticals = True
            self.shortoutput = '{num} queues are not ready !'.format(
                num=len(failed_status))
            for fail in failed_status:
                self.longoutput.append(
                    'Queue: {QueueIdentity}, Status: {Status}'.format(**fail))
        else:
            # Check for high message count in queues
            for obj in xml:
                if obj['MessageCount'] >= self.options.critical:
                    self.add_critical_result(obj)
                elif obj['MessageCount'] >= self.options.warning:
                    self.add_warning_result(obj)
            self._prepare_output(problem_pattern='There are {num} queues with '
                                                 'more than {thr} messages',
                                 ok_pattern='All queues are normal.')

        # Add performance data
        for obj in xml:
            self.perfdata.append(
                '\'{QueueIdentity}\'={MessageCount}msg;{warn};{crit};0;'.format(
                    warn=self.options.warning,
                    crit=self.options.critical,
                    **obj))

        # Exit
        if self.have_criticals:
            self.critical(self.output())
        elif self.have_warnings:
            self.warning(self.output())
        else:
            self.ok(self.output())

    def _prepare_output(self, problem_pattern, ok_pattern):
        """Prepare the message output shown in Nagios."""
        shortoutput = []
        if self.have_criticals or self.have_warnings:
            for severity in sorted(self._alerts.keys()):
                num_alerts = len(self._alerts[severity])
                if num_alerts:
                    shortoutput.append(
                        problem_pattern.format(num=num_alerts,
                                               thr=getattr(self.options,
                                                           severity)))
                    self.longoutput.append(
                        '====== {} ======'.format(severity.upper()))
                    for result in self._alerts[severity]:
                        details = '{QueueIdentity}: ' \
                                  '{MessageCount} messages'.format(**result)
                        self.longoutput.append(details)
            self.shortoutput = ', '.join(shortoutput)
        else:
            self.shortoutput = ok_pattern

    def define_plugin_arguments(self):
        """Extra plugin arguments."""
        super(PluginXMLHUB, self).define_plugin_arguments()
        self.required_args.add_argument(
            '-w',
            dest='warning',
            type=int,
            help='Max message count in a queue before warning.',
            required=True)

        self.required_args.add_argument(
            '-c',
            dest='critical',
            type=int,
            help='Max message count in a queue before critical.',
            required=True)

    def verify_plugin_arguments(self):
        super(PluginXMLHUB, self).verify_plugin_arguments()
        if self.options.warning >= self.options.critical:
            self.unknown('Warning threshold cannot be >= critical !')
