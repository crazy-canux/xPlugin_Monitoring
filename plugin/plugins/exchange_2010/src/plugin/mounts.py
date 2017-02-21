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

"""Class definition for MOUNTPOINTS check plugins."""

import logging

from .base import PluginBase

logger = logging.getLogger('plugin.mounts')


class PluginXMLMounts(PluginBase):
    """Plugin class for Mountpoints check plugin."""
    def __init__(self, *args, **kwargs):
        super(PluginXMLMounts, self).__init__(*args, **kwargs)

    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()
        warn_used = 100 - self.options.warning
        crit_used = 100 - self.options.critical

        logger.debug('Warning used space threshold: %d', warn_used)
        logger.debug('Critical used space threshold: %d', crit_used)

        for mount in xml:
            free_space = int(mount['Free(%)'])
            used_space = 100 - free_space

            logger.debug('Analyzing mount point: %s', mount['Label'])
            logger.debug('== Free space: %d %%', free_space)
            logger.debug('== Used space: %d %%', used_space)

            # Tests against thresholds
            if free_space <= self.options.critical:
                self.add_critical_result(mount)
            elif free_space <= self.options.warning:
                self.add_warning_result(mount)

            # Perfdata
            self.perfdata.append(
                '\'{datasource}\'={value}%;{warn};{crit};0;100;'.format(
                    datasource=mount['Label'],
                    value=used_space,
                    warn=warn_used,
                    crit=crit_used))

        # Exit
        self._prepare_output(
            problem_pattern='{num} mountpoints with less than '
                            '{thr}% free space',
            ok_pattern='All mountpoints have enough free space available.')
        if self.have_criticals:
            self.critical(self.output())
        elif self.have_warnings:
            self.warning(self.output())
        else:
            self.ok(self.output())

    def define_plugin_arguments(self):
        """Extra plugin arguments."""
        super(PluginXMLMounts, self).define_plugin_arguments()

        self.required_args.add_argument(
            '-w',
            dest='warning',
            type=int,
            help='Free space warning threshold in percent.',
            required=True)

        self.required_args.add_argument(
            '-c',
            dest='critical',
            type=int,
            help='Free space critical threshold in percent.',
            required=True)

    def verify_plugin_arguments(self):
        super(PluginXMLMounts, self).verify_plugin_arguments()
        if not self.options.warning > self.options.critical:
            self.unknown('Warning threshold must be < critical ! '
                         'We are checking the free space here.')

    def _prepare_output(self, problem_pattern, ok_pattern):
        """Prepare the message output shown in Nagios."""
        shortoutput = []
        if self.have_criticals or self.have_warnings:
            for severity in sorted(self._alerts.keys()):
                shortoutput.append(
                    problem_pattern.format(num=len(self._alerts[severity]),
                                       thr=getattr(self.options, severity)))
                self.longoutput.append('====== {} ======'.format(
                    severity.upper()))
                for result in self._alerts[severity]:
                    details = '{Label}: {Free(%)}%'.format(**result)
                    self.longoutput.append(details)
            self.shortoutput = ', '.join(shortoutput)
        else:
            self.shortoutput = ok_pattern
