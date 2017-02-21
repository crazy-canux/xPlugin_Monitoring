#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""Copyright (C) Canux CHENG <canuxcheng@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys
import logging
import argparse
import pymssql
import datetime


class Nagios(object):

    """Basic class for nagios."""

    def __init__(self, name=None, version='1.0.0', description='For e-supply'):
        self.__name = os.path.basename(sys.argv[0]) if not name else name
        self.__version = version
        self.__description = description

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("e-supply")
        self.logger.setLevel(logging.INFO)

        # Init the argument
        self.__define_options()
        self.define_sub_options()
        self.__parse_options()

        # Init the logger
        if self.args.debug:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug("===== BEGIN DEBUG =====")
        self.logger.debug("Init Nagios")

        # Init output data.
        self.output_ = ""
        self.shortoutput = ""
        self.longoutput = []
        self.perfdata = []

        # End the debug.
        if self.__class__.__name__ == "Nagios":
            self.logger.debug("===== END DEBUG =====")

    def __define_options(self):
        self.parser = argparse.ArgumentParser(description="Plugin for e-supply.")
        self.parser.add_argument('-V', '--version',
                                 action='version',
                                 version='%s %s' % (self.__name,
                                                    self.__version),
                                 help='Show version')
        self.parser.add_argument('-D', '--debug',
                                 action='store_true',
                                 required=False,
                                 help='Show debug informations.',
                                 dest='debug')

    def define_sub_options(self):
        self.mssql_parser = self.parser.add_argument_group('E-supply options',
                                                           'For db connect.')
        self.subparsers = self.parser.add_subparsers(title='Action:',
                                                     description='The mode.',
                                                     help='Options for mode.')

    def __parse_options(self):
        try:
            self.args = self.parser.parse_args()
        except Exception as e:
            self.unknown("parser args error: %s" % e)

    def output(self, substitute=None, long_output_limit=20):
        if not substitute:
            substitute = {}

        self.output_ += "{0}".format(self.shortoutput)
        if self.longoutput:
            self.output_ = self.output_.rstrip("\n")
            self.output_ += "\n{0}".format(
                "\n".join(self.longoutput[:long_output_limit]))
            if long_output_limit:
                self.output_ += "\n(...showing only first {0} lines, " \
                    "{1} elements remaining...)".format(
                        long_output_limit,
                        len(self.longoutput[long_output_limit:]))
        if self.perfdata:
            self.output_ = self.output_.rstrip("\n")
            self.output_ += " | {0}".format(" ".join(self.perfdata))
        return self.output_.format(**substitute)

    def ok(self, msg):
        raise NagiosOk(msg)

    def warning(self, msg):
        raise NagiosWarning(msg)

    def critical(self, msg):
        raise NagiosCritical(msg)

    def unknown(self, msg):
        raise NagiosUnknown(msg)


class NagiosOk(Exception):

    def __init__(self, msg):
        print "OK - %s" % msg
        raise SystemExit(0)


class NagiosWarning(Exception):

    def __init__(self, msg):
        print "WARNING - %s" % msg
        raise SystemExit(1)


class NagiosCritical(Exception):

    def __init__(self, msg):
        print "CRITICAL - %s" % msg
        raise SystemExit(2)


class NagiosUnknown(Exception):

    def __init__(self, msg):
        print "UNKNOWN - %s" % msg
        raise SystemExit(3)


class Mssql(Nagios):

    """Basic class for mssql."""

    def __init__(self, *args, **kwargs):
        super(Mssql, self).__init__(*args, **kwargs)
        self.logger.debug("Init mssql")
        try:
            self.conn = pymssql.connect(server=self.args.server,
                                        user=self.args.user,
                                        password=self.args.password,
                                        database=self.args.database,
                                        timeout=self.args.timeout,
                                        login_timeout=self.args.login_timeout,
                                        charset=self.args.charset,
                                        as_dict=self.args.as_dict)
        except pymssql.Error as e:
            self.unknown("Can not connect to the mssql: %s" % e)

    def query(self, sql_query):
        try:
            self.cursor = self.conn.cursor()
            self.logger.debug("get cursor ok")
        except pymssql.Error as e:
            self.unknown("Get cursor error: %s" % e)
        try:
            self.logger.debug("sql: {}".format("".join(sql_query)))
            self.cursor.execute("".join(sql_query))
            self.logger.debug("execute ok")
        except pymssql.Error as e:
            self.unknown("Execute sql error: %s" % e)
        try:
            self.results = self.cursor.fetchall()
            self.logger.debug("fetchall ok")
        except pymssql.Error as e:
            self.unknown("Fetchall error: %s" % e)
        try:
            self.cursor.close()
            self.logger.debug("Close cursor ok")
        except pymssql.Error as e:
            self.unknown("Close cursor error: %s" % e)
        return self.results

    def close(self):
        """Close the connection."""
        try:
            self.conn.close()
            self.logger.debug("Close connect ok")
        except pymssql.Error as e:
            self.unknown("Close connect error: %s" % e)

    def define_sub_options(self):
        super(Mssql, self).define_sub_options()
        self.mssql_parser.add_argument('-H', '--server',
                                       required=True,
                                       help='database server\instance.',
                                       dest='server')
        self.mssql_parser.add_argument('-u', '--user',
                                       required=True,
                                       help='database username.',
                                       dest='user')
        self.mssql_parser.add_argument('-p', '--password',
                                       required=True,
                                       help='database password.',
                                       dest='password')
        self.mssql_parser.add_argument('-d', '--database',
                                       default='master',
                                       required=False,
                                       help='database name, default master',
                                       dest='database')
        self.mssql_parser.add_argument('-t', '--timeout',
                                       default=30,
                                       type=int,
                                       required=False,
                                       help='query timeout, default 30s',
                                       dest='timeout')
        self.mssql_parser.add_argument('-l', '--login_timeout',
                                       default=60,
                                       type=int,
                                       required=False,
                                       help='connection and login time out,\
                                       default 60s.',
                                       dest='login_timeout')
        self.mssql_parser.add_argument('-c', '--charset',
                                       default='utf8',
                                       type=str,
                                       required=False,
                                       help='set the charset, default utf8',
                                       dest='charset')


class TimeCheck(Mssql):

    """For e-supply function monitoring."""

    def __init__(self, *args, **kwargs):
        super(TimeCheck, self).__init__(*args, **kwargs)
        self.logger.debug("Init TimeCheck")

    def define_sub_options(self):
        super(TimeCheck, self).define_sub_options()
        self.sql_parser = self.subparsers.add_parser('timecheck',
                                                     help='esupply function monitoring .',
                                                     description='Options\
                                                     for esupply.')
        self.sql_parser.add_argument('-w', '--warning',
                                     default=0,
                                     type=int,
                                     required=False,
                                     help='Warning minutes, default is %(default)s',
                                     dest='warning')
        self.sql_parser.add_argument('-c', '--critical',
                                     default=0,
                                     type=int,
                                     required=False,
                                     help='Critical minutes, default is %(default)s',
                                     dest='critical')
        self.sql_parser.add_argument('--as_dict',
                                     default=False,
                                     type=bool,
                                     required=False,
                                     help='Set the return mode.',
                                     dest='as_dict')

    def timecheck_handle(self):
        self.sql = "select create_date, location from error_log where type='technical' and sub_type='Scheduler'"
        status = self.ok
        self.shortoutput = "Create_date already up to date."

        self.__results = self.query(self.sql)
        self.logger.debug("results: {}".format(self.__results))
        # [(datetime.datetime(2016, 9, 9, 14, 41, 15), u'Server: Ip46_Scheduler-Tirgger'), (datetime.datetime(2016, 9, 9, 14, 41, 15), u'Server: Ip46_Scheduler-Tirgger')]
        self.close()
        if self.__results:
            self.longoutput.append("-------------------------------\n")
            for create_date, location in self.__results:
                self.logger.debug("create_date: {}".format(create_date))
                self.logger.debug("location: {}".format(location))
                current_datetime = datetime.datetime.now()
                self.logger.debug("current_datetime: {}".format(current_datetime))
                self.longoutput.append("create_date: " + str(create_date) + "\n" + "location: " + str(location) + "\n")
                if current_datetime - create_date > datetime.timedelta(minutes=self.args.warning):
                    status = self.warning
                    self.shortoutput = "Create_date not update in {} min".format(self.args.warning)
                if current_datetime - create_date > datetime.timedelta(minutes=self.args.critical):
                    status = self.critical
                    self.shortoutput = "Create_date not update in {} min".format(self.args.critical)
        else:
            self.shortoutput = "Everything up to date"

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class Esupply(Mssql):

    """Count the return value and show the lines.

    Monitoring e-supply process.

    """

    def __init__(self, *args, **kwargs):
        super(Esupply, self).__init__(*args, **kwargs)
        self.logger.debug("Init esupply")

    def define_sub_options(self):
        super(Esupply, self).define_sub_options()
        self.esupply_parser = self.subparsers.add_parser('esupply',
                                                         help='For esupply db',
                                                         description='Options\
                                                         for esupply.')
        self.esupply_parser.add_argument('-s', '--sql',
                                         action='append',
                                         type=str,
                                         required=True,
                                         help='The sql or store procedure.',
                                         dest='sql')
        self.esupply_parser.add_argument('-w', '--warning',
                                         default=0,
                                         type=int,
                                         required=False,
                                         help='Warning value for sql',
                                         dest='warning')
        self.esupply_parser.add_argument('-c', '--critical',
                                         default=0,
                                         type=int,
                                         required=False,
                                         help='Critical value for sql',
                                         dest='critical')
        self.esupply_parser.add_argument('--as_dict',
                                         default=True,
                                         type=bool,
                                         required=False,
                                         help='Set the return mode.',
                                         dest='as_dict')

    def esupply_handle(self):
        self.__results = self.query(self.args.sql)
        self.close()
        self.logger.debug("results: {}".format(self.__results))
        self.__result = int(len(self.__results))
        self.logger.debug("result: {}".format(self.__result))
        status = self.ok

        # Compare the vlaue.
        if self.__result > self.args.warning:
            status = self.warning
        if self.__result > self.args.critical:
            status = self.critical

        # Output for nagios
        self.shortoutput = "The result is {}".format(self.__result)
        self.longoutput.append("-------------------------------\n")
        if self.__result:
            if isinstance(self.__results[0], dict):
                keys = self.__results[0].keys()
                for loop in range(0, self.__result):
                    for key in keys:
                        value = str(self.__results[loop].get(key)).strip("\n")
                        line = key + ": " + value
                        self.longoutput.append(line + "\n")
                    self.longoutput.append("-------------------------------\n")
        self.perfdata.append("\n{sql}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=self.__result,
            sql=self.args.sql))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class Diff(TimeCheck, Esupply):

    """Summary all function monitoring class."""

    def __init__(self, *args, **kwargs):
        super(Diff, self).__init__(*args, **kwargs)


def main():
    plugin = Diff()
    arguments = sys.argv[1:]
    if 'timecheck' in arguments:
        plugin.timecheck_handle()
    elif 'esupply' in arguments:
        plugin.esupply_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
