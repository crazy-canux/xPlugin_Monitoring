#!/usr/bin/env python2.7
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
from monitoring.nagios.plugin import NagiosPluginHTTP
from bs4 import BeautifulSoup
import tempfile
import traceback
import time
import sys

logger = logging.getLogger('plugin')


# Define new args
class PluginLicman(NagiosPluginHTTP):
    """Customize plugin behavior."""
    def define_plugin_arguments(self):
        super(PluginLicman, self).define_plugin_arguments()
        self.required_args.add_argument('-s', '--search',
                                        dest="search",
                                        required=False,
                                        default="EXPIRES=01-Jul-2016",
                                        help="The search string. \
                                        Include the expiration time. \
                                        Default value is EXPIRES=01-Jul-2016.")
        self.required_args.add_argument('-w', '--warning',
                                        dest='warning',
                                        type=int,
                                        help='File should be updated before '
                                             'this number of days.',
                                        default=30,
                                        required=False)
        self.required_args.add_argument('-c', '--critical',
                                        dest='critical',
                                        type=int,
                                        help='File should be updated before '
                                             'this number of days.',
                                        default=5,
                                        required=False)


# Use this dict to get the number of the month.
month_dict = {
    "Jan": lambda: 1,
    "Feb": lambda: 2,
    "Mar": lambda: 3,
    "Apr": lambda: 4,
    "May": lambda: 5,
    "Jun": lambda: 6,
    "Jul": lambda: 7,
    "Aug": lambda: 8,
    "Sep": lambda: 9,
    "Oct": lambda: 10,
    "Nov": lambda: 11,
    "Dec": lambda: 12
}


def main():
    reload(sys)
    sys.setdefaultencoding("utf-8")

    plugin = PluginLicman(version='1.0.0',
                          description='Checks the licence expiration.')

    # Final status exit for the plugin
    status = None

    try:
        # Get the text.
        response = plugin.http.get(plugin.options.path)
        soup = BeautifulSoup(response.text)
        logger.debug("soup: {}".format(soup))
        info = soup.get_text()
        logger.debug("info: {}".format(info))
        temp = tempfile.TemporaryFile("w+r")
        temp.writelines(info)
        temp.seek(0)
        lines = temp.readlines()
        logger.debug("lines: {}".format(lines))

        # If the search string exist.
        for line in lines:
            logger.debug("line: {}".format(line))
            if plugin.options.search in line:
                status = plugin.ok
                exp_time = plugin.options.search.split("=")[1].split("-")
                logger.debug("exp_time: {}".format(exp_time))
                day = exp_time[0]
                month = month_dict[exp_time[1]]()
                year = exp_time[2]
                exp_sec = time.mktime((int(year), int(month), int(day),
                                       0, 0, 0, 0, 0, 0))
                logger.debug("exp_sec: {}".format(exp_sec))
                now_sec = time.time()
                logger.debug("now_sec: {}".format(now_sec))
                diff_sec = exp_sec - now_sec
                logger.debug("diff_sec: {}".format(diff_sec))
                warn_sec = plugin.options.warning * 24 * 60 * 60
                logger.debug("warn_sec: {}".format(warn_sec))
                crit_sec = plugin.options.critical * 24 * 60 * 60
                logger.debug("crit_sec: {}".format(crit_sec))

                # Check threshold.
                if plugin.options.warning:
                    if diff_sec <= warn_sec:
                        status = plugin.warning
                if plugin.options.critical:
                    if diff_sec <= crit_sec:
                        status = plugin.critical

                # Output information.
                if diff_sec <= 0:
                    plugin.shortoutput = "The licence to be overdue."
                elif diff_sec > 0:
                    day = (diff_sec / 60 / 60 / 24)
                    plugin.shortoutput = "The licence can use {} days.".format(
                        day)
                break
            else:
                status = plugin.critical
                plugin.shortoutput = "Can not find {}.".format(
                    plugin.options.search)

        # Exit the plugin.
        status(plugin.output())
        logger.debug("Return status and exit to Nagios.")

    except Exception:
        plugin.shortoutput = "Something unexpected happend!" \
            "Please investigate..."
        plugin.longoutput = traceback.format_exc().splitlines()
        plugin.unknown(plugin.output())

if __name__ == "__main__":
    main()
