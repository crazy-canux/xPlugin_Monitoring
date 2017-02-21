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

import logging
import datetime

from .base import ExaleadBase


logger = logging.getLogger("plugin.exalead.plugin")


class ExaleadBuildGroup(ExaleadBase):
    """
    Exalead plugin that check buildgroup status.
    """
    def initialize(self):
        super(ExaleadBuildGroup, self).initialize()

        self.buildgroup = self.options.buildgroup
        self.limit_ndocs = self.options.limit_number_documents
        self.url = \
            'http://{0}:{1}/mami/indexing/getBuildGroupStatus' \
            '?buildGroup={2}'.format(self.host, self.port, self.buildgroup)

        # Construct commit age time delta object
        limit_commit_age_parts = (int(part) for part
                                  in self.options.limit_commit_age.split(','))
        self.limit_commit_age = datetime.timedelta(*limit_commit_age_parts)

        logger.debug('Plugin attributes:')
        logger.debug(
            '\tArg: limit_commit_age: {0}'.format(
                self.options.limit_commit_age))
        logger.debug(
            '\tCommit age time delta object: {0}'.format(
                self.limit_commit_age))

    def define_plugin_arguments(self):
        """Define specific plugin arguments"""
        super(ExaleadBuildGroup, self).define_plugin_arguments()

        self.required_args.add_argument(
            '-b', '--buildgroup',
            dest='buildgroup',
            help='Build group name to check',
            required=True)
        self.required_args.add_argument(
            '--limit-ndocs',
            type=int,
            dest='limit_number_documents',
            help='Threshold for number of documents in checked build group. '
                 'Return WARNING if below.',
            required=True)
        self.required_args.add_argument(
            '--commit-age',
            dest='limit_commit_age',
            help="Threshold for last commit date age. Format: [days[, "
                 "seconds[, microseconds[, milliseconds[, minutes[, hours[, "
                 "weeks]]]]]]]. Return WARNING if last commit date is older.",
            required=True)


class ExaleadDeployment(ExaleadBase):
    """
    Exalead plugin that check deployment states.
    """
    def initialize(self):
        """Plugin initialization"""
        super(ExaleadDeployment, self).initialize()

        self.url = \
            'http://{0}:{1}/mami/deploy/getDeploymentStatus'.format(self.host,
                                                                    self.port)