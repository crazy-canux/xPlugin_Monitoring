#!/usr/bin/env python2.7
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
import re
from pprint import pformat
from datetime import datetime

import nemo
from nemo.job import NemoPluginJob


logger = logging.getLogger('plugin.nemo.job')

# Init plugin
plugin = NemoPluginJob(version=nemo.__version__,
                       description="Check for outdated jobs" )

# Final status exit for the plugin
status = None

#Attrs
job_age = None
cwd_age = None
cwd_last_modified = None
jobs_with_old_jobs = plugin.xml.find_all('job',
                                         starttime=re.compile(r'[^-]'),
                                         finishtime='-')

#Are there any old jobs with an old logfile ?
for j in jobs_with_old_jobs:
    job_age = datetime.now() - datetime.fromtimestamp(float(j['starttime']))

    if job_age > plugin.options.max_job_age:
        cwd_last_modified = datetime.fromtimestamp(
            plugin.ssh.get_file_lastmodified_timestamp(j['cwd']))
        cwd_age = datetime.now() - cwd_last_modified

        if cwd_age > plugin.options.max_cwd_age:
            plugin.inactive_cwd.append(j)

logger.debug("Found inactive cwd: \n%s", pformat(plugin.inactive_cwd))

#Checks for nagios status
if not cwd_age:
    status = plugin.ok
    plugin.shortoutput = "Jobs are RUNNING well."

if plugin.inactive_cwd:
    status = plugin.critical
    plugin.shortoutput = "{0} jobs outdated (> {1} hours) " \
                         "with an old logfile (> {2} hours).".format(
                         len(plugin.inactive_cwd),
                         plugin.options.max_job_age,
                         plugin.options.max_cwd_age)

# Set longoutput with name of logfiles
for j in plugin.inactive_cwd:
    plugin.longoutput.append(
        "{0[host]}: {0[jobname]} (ID: {0[jobid]}) - "
        "Logfile path : {0[cwd]}".format(j))

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please '
                   'investigate with debug mode on.')
