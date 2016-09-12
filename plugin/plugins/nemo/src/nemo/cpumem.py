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

from base import NemoPlugin


logger = logging.getLogger('plugin.nemo.base')


class NemoPluginCpuMem(NemoPlugin):
    """
    Args for check CPU and MEM
        warning - Warning threshold in percent
        critical - Critical threshold in percent
        mode - Mode of operation : ['cpu', 'mem']
        job_critical - Critical threshold in percent if a job queue nemo_* is running
    """

    def define_plugin_arguments(self):
        super(NemoPluginCpuMem,self).define_plugin_arguments()

        self.required_args.add_argument('-w',
                                        dest="warning",
                                        type=int,
                                        help="Warning threshold in percent.",
                                        required=True)

        self.required_args.add_argument('-c',
                                        dest="critical",
                                        type=int,
                                        help="Critical threshold in percent.",
                                        required=True)
        self.required_args.add_argument('--mode',
                                        dest="mode",
                                        choices=['cpu', 'mem'],
                                        help="Mode of operation : check CPU or "
                                             "MEMORY",
                                        required=True)

        self.required_args.add_argument('--job_critical',
                                        dest="job_critical",
                                        type=int,
                                        default=10,
                                        help="Critical threshold in percent if "
                                             "a job queue nemo_* is running.",
                                        required=False)

    def verify_plugin_arguments(self):
        super(NemoPluginCpuMem, self).verify_plugin_arguments()

        if self.options.warning >= self.options.critical:
            self.unknown('Warning threshold cannot be higher than critical !')

        if not self.options.warning in range(0, 101):
            self.unknown('Warning threshold must be between 0 to 100 !')
        
        if not self.options.critical in range(0, 101):
            self.unknown('Critical threshold must be between 0 to 100 !')

    def initialize(self):
        super(NemoPluginCpuMem,self).initialize()

        # Attrs
        self.jobs_in_nemo_queues = False

        # Are there any jobs in nemo queues ?
        if self.xml.find_all('job', status='RUN', queue=NemoPlugin.job_queue):
            self.jobs_in_nemo_queues = True

        logger.debug("jobs_in_nemo_queues : {0}".format(
            self.jobs_in_nemo_queues))
