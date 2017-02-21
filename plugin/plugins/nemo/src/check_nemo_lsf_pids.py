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

import nemo
from nemo.pid import NemoPluginPid
import logging
from pprint import pformat

logger = logging.getLogger('plugin.nemo.pid')

# Init plugin
plugin = NemoPluginPid(version=nemo.__version__, description="Check if a PID is empty on a RUNNING job with queues=\"nemo_*\"")

# Final status exit for the plugin
status = None

# Attrs
jobs_in_nemo_pids = False
oids = {
    'hrSWRunName': '1.3.6.1.2.1.25.4.2.1.2',
}

snmpquery = plugin.snmp.getnext(oids)
logger.debug("result of SNMPWALK : {0}".format(snmpquery))

# Are there any jobs with an empty PIDS ?
logger.debug("jobs_in_nemo_pids : {0}".format(jobs_in_nemo_pids))

host_tag = plugin.xml.find('host', hostname=plugin.options.slave.lower())
jobs_with_empty_pid = plugin.xml.find_all('job', host=host_tag['hostname'], status='RUN', pids='', queue=NemoPluginPid.job_queue)
jobs_with_pid = plugin.xml.find_all('job', host=host_tag['hostname'], status='RUN', pids=NemoPluginPid.empty_pid, queue=NemoPluginPid.job_queue)

# Check existing PIDs
for job in jobs_with_pid:
    pids = job['pids'].split(',')

    for pid in pids:
        pid_found = False
        for process in snmpquery['hrSWRunName']:
            if process.index == pid:
                pid_found = True
                break

        if not pid_found:
            plugin.missing_pids.append({'job': job, 'pid': pid})

logger.debug('Process details for running PID:\n%s', pformat(plugin.missing_pids, indent=4))

# Check status in Nagios
if plugin.missing_pids:
    status = plugin.critical
    plugin.shortoutput = "{} jobs with missing PID !".format(len(plugin.missing_pids))
    for pid in plugin.missing_pids:
        plugin.longoutput.append("Job \"{job[jobname]}\" has no process with PID {pid}".format(job=pid['job'], pid=pid['pid']))
elif jobs_with_empty_pid:
    status = plugin.warning
    plugin.shortoutput = "{} jobs with empty PID !".format(len(jobs_with_empty_pid))
    for j in jobs_with_empty_pid:
        plugin.longoutput.append("{0[jobname]} (Job ID: {0[jobid]})".format(j))
else:
    status = plugin.ok
    plugin.shortoutput = "Slave {} is running his jobs normally.".format(host_tag['hostname'])

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
