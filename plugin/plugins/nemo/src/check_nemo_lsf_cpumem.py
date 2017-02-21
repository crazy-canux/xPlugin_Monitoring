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
import nemo
from nemo.cpumem import NemoPluginCpuMem

logger = logging.getLogger('plugin.cpumem')

# Init plugin
plugin = NemoPluginCpuMem(version=nemo.__version__, description="Check CPU or MEMORY with XML file" )

# Final status exit for the plugin
status = None

#Attrs
value = None
host_tag = plugin.xml.find('host', hostname=plugin.options.hostname)
host_run_jobs = plugin.xml.find_all('job', host=host_tag['hostname'], status='RUN')
mode = {
    'cpu': 'ut',
    'mem': 'mem',
}

#Are there any hight utilisation of CPU or Memory ?
if host_tag:
    raw_value = float(host_tag[mode[plugin.options.mode]])

    if plugin.options.mode == 'mem':
        maxmem = float(host_tag['maxmem'])
        value = ( raw_value * 100 ) / maxmem
    else:
        value = raw_value

    if value < plugin.options.job_critical and not value > plugin.options.warning:
        if plugin.jobs_in_nemo_queues:
            status = plugin.critical
            plugin.shortoutput = "Jobs are running in queue nemo_*, but {0} is'nt >= {1:.2f} %".format(plugin.options.mode.upper(), plugin.options.job_critical)
    else:
        if value < plugin.options.warning:
            status = plugin.ok
            plugin.shortoutput = "{0} is {1:.2f} %".format(plugin.options.mode.upper(), value)
        elif value < plugin.options.critical:
            if plugin.options.mode == 'mem' and host_run_jobs:
                status = plugin.ok
                plugin.longoutput.append('Skipping Memory Warning. {} jobs are running on host.'.format(len(host_run_jobs)))
            else:
                status = plugin.warning
            plugin.shortoutput = "{0} is {1:.2f} %".format(plugin.options.mode.upper(), value)
        else:
            if plugin.options.mode == 'mem' and host_run_jobs:
                status = plugin.ok
                plugin.longoutput.append('Skipping Memory Critical. {} jobs are running on host.'.format(len(host_run_jobs)))
            else:
                status = plugin.critical
            plugin.shortoutput = "{0} is {1:.2f} %".format(plugin.options.mode.upper(), value)

    logger.debug('{0.hostname} {0.mode} is: {1:.2f} %'.format(plugin.options, value))
else:
    plugin.unknown('Host {0.hostname} is not found !'.format(plugin.options))

# Performance data
plugin.perfdata.append('{0.mode}={1:.2f}%;{0.warning};{0.critical};0;100;'.format(
    plugin.options,
    value,
))

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output())
else:
    plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
