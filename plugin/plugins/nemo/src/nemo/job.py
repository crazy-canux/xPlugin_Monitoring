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

from monitoring.nagios.plugin import NagiosPluginSSH
from monitoring.nagios.plugin import argument

from base import NemoPlugin


class NemoPluginJob(NemoPlugin, NagiosPluginSSH):
    """
    Args for check jobs
        max_job_age - job age in hours
        max_cwd_age - cwd age in hours
    """

    def define_plugin_arguments(self):
        super(NemoPluginJob,self).define_plugin_arguments()

        self.required_args.add_argument('--max_job_age',
                                        dest="max_job_age",
                                        type=argument.hours,
                                        default="3",
                                        help="(Optional) Jobs age in hours "
                                             "(default is 3)",
                                        required=False)

        self.required_args.add_argument('--max_cwd_age',
                                        dest="max_cwd_age",
                                        type=argument.hours,
                                        default="1",
                                        help="(Optional) cwd age in hours "
                                             "(default is 1)",
                                        required=False)

    def initialize(self):
        super(NemoPluginJob, self).initialize()

        self.inactive_cwd = []
