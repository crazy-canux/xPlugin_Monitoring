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
from monitoring.nagios.plugin import NagiosPluginMSSQL

logger = logging.getLogger('plugin.sql')


# define new args
class PluginSQL(NagiosPluginMSSQL):
    def define_plugin_arguments(self):
        super(PluginSQL, self).define_plugin_arguments()

        self.required_args.add_argument("-S", "--sql",
                                        dest="sql",
                                        required=True,
                                        help="sql query for mssql.")
        self.required_args.add_argument("-w", "--warning",
                                        type=int,
                                        dest="warning",
                                        default=0,
                                        required=False,
                                        help="Warning value.")
        self.required_args.add_argument("-c", "--critical",
                                        type=int,
                                        dest="critical",
                                        default=0,
                                        required=False,
                                        help="Critical value.")


def main():
    # Init plugin
    plugin = PluginSQL(version="1.0",
                       description="Run a sql for mssql.")

    # Final status exit for the plugin
    status = None

    # MSSQL version.
    sql_output = plugin.query('SELECT @@VERSION')
    plugin.close()
    logger.debug("MSSQL version: {}".format(sql_output))

    # SQL query
    sql_output = plugin.query(plugin.options.sql)
    plugin.close()
    result = int(len(sql_output))
    logger.debug("sql: {}".format(plugin.options.sql))
    logger.debug("sql_output: {}".format(sql_output))
    logger.debug("result: {}".format(result))

    status = plugin.ok

    # Compare the vlaue.
    if result > plugin.options.warning:
        status = plugin.warning
    if result > plugin.options.critical:
        status = plugin.critical

    # Output for nagios
    plugin.shortoutput = "The result is {}".format(result)
    plugin.longoutput.append("-------------------------------\n")
    if result:
        if isinstance(sql_output[0], dict):
            keys = sql_output[0].keys()
            logger.debug("keys: {}".format(keys))
            for loop in range(0, len(sql_output)):
                for key in keys:
                    value = str(sql_output[loop].get(key)).strip("\n")
                    line = key + ": " + value
                    plugin.longoutput.append(line + "\n")
                plugin.longoutput.append("-------------------------------\n")
            logger.debug("longoutput: {}".format(plugin.longoutput))
    plugin.perfdata.append("\n{sql}={result};{warn};{crit};0;".format(
        crit=plugin.options.critical,
        warn=plugin.options.warning,
        result=result,
        sql=plugin.options.sql))

    # Return status with message to Nagios.
    status(plugin.output(long_output_limit=None))
    logger.debug("Return status and exit to Nagios.")

if __name__ == "__main__":
    main()
