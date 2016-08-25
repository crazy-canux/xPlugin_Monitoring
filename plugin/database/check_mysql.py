#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Copyright (C) 2015 Faurecia (China) Holding Co.,Ltd.

All rights reserved.
Name: check_mysql.py
Author: Canux CHENG canuxcheng@gmail.com
Version: V1.0.0.0
Time: Wed 27 Jul 2016 02:32:05 PM CST

Description:
    [1.0.0.0] 20160727 Init this plugin for basic functions.
"""
import os
import sys
import logging
import argparse
# try:
#     import cPickle as pickle
# except:
#     import pickle

import pymysql.cursors


class Nagios(object):

    """Basic class for nagios."""

    def __init__(self, name=None, version='1.0.0', description='For mysql'):
        self.__name = os.path.basename(sys.argv[0]) if not name else name
        self.__version = version
        self.__description = description

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("mysql")
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
        self._output = ""
        self.shortoutput = ""
        self.longoutput = []
        self.perfdata = []

        # End the debug.
        if self.__class__.__name__ == "Nagios":
            self.logger.debug("===== END DEBUG =====")

    def __define_options(self):
        self.parser = argparse.ArgumentParser(description="Plugin for mysql.")
        self.parser.add_argument('-V', '--version',
                                 action='version',
                                 version='{0} {1}'.format(self.__name, self.__version),
                                 help='Show version')
        self.parser.add_argument('-D', '--debug',
                                 action='store_true',
                                 required=False,
                                 help='Show debug informations.',
                                 dest='debug')

    def define_sub_options(self):
        self.mysql_parser = self.parser.add_argument_group('mysql options',
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

        self._output += "{0}".format(self.shortoutput)
        if self.longoutput:
            self._output = self._output.rstrip("\n")
            self._output += "\n{0}".format(
                "\n".join(self.longoutput[:long_output_limit]))
            if long_output_limit:
                self._output += "\n(...showing only first {0} lines, " \
                    "{1} elements remaining...)".format(
                        long_output_limit,
                        len(self.longoutput[long_output_limit:]))
        if self.perfdata:
            self._output = self._output.rstrip("\n")
            self._output += " | {0}".format(" ".join(self.perfdata))
        return self._output.format(**substitute)

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


class Mysql(Nagios):

    """Basic class for mysql."""

    def __init__(self, *args, **kwargs):
        super(Mysql, self).__init__(*args, **kwargs)
        self.logger.debug("Init mysql")
        try:
            self.conn = pymysql.connect(host=self.args.host,
                                        user=self.args.user,
                                        password=self.args.password,
                                        database=self.args.database,
                                        connect_timeout=self.args.login_timeout,
                                        charset=self.args.charset,
                                        cursorclass=self.args.as_dict)
        except pymysql.Error as e:
            self.unknown("Can not connect to the mysql: %s" % e)

    def query(self, sql_query):
        try:
            self.cursor = self.conn.cursor()
            self.logger.debug("get cursor ok")
        except pymysql.Error as e:
            self.unknown("Get cursor error: %s" % e)
        try:
            self.logger.debug("sql: {}".format("".join(sql_query)))
            self.cursor.execute("".join(sql_query))
            self.logger.debug("execute ok")
        except pymysql.Error as e:
            self.unknown("Execute sql error: %s" % e)
        try:
            self.results = self.cursor.fetchall()
            self.logger.debug("fetchall ok")
        except pymysql.Error as e:
            self.unknown("Fetchall error: %s" % e)
        try:
            self.cursor.close()
            self.logger.debug("Close cursor ok")
        except pymysql.Error as e:
            self.unknown("Close cursor error: %s" % e)
        return self.results

    def close(self):
        """Close the connection."""
        try:
            self.conn.close()
            self.logger.debug("Close connect ok")
        except pymysql.Error as e:
            self.unknown("Close connect error: %s" % e)

    def define_sub_options(self):
        super(Mysql, self).define_sub_options()
        self.mysql_parser.add_argument('-H', '--host',
                                       required=True,
                                       help='database server\instance.',
                                       dest='host')
        self.mysql_parser.add_argument('-u', '--user',
                                       required=True,
                                       help='database username.',
                                       dest='user')
        self.mysql_parser.add_argument('-p', '--password',
                                       required=True,
                                       help='database password.',
                                       dest='password')
        self.mysql_parser.add_argument('-d', '--database',
                                       default='master',
                                       required=False,
                                       help='database name, default is %(default)s',
                                       dest='database')
        self.mysql_parser.add_argument('-l', '--login_timeout',
                                       default=60,
                                       type=int,
                                       required=False,
                                       help='connection and login time out, default is %(default)s',
                                       dest='login_timeout')
        self.mysql_parser.add_argument('-c', '--charset',
                                       default='utf8',
                                       type=str,
                                       required=False,
                                       help='set the charset, default is %(default)s',
                                       dest='charset')


# Extension for function monitoring.
# Just use the API from class Nagios and mysql.


class Sql(Mysql):

    """Just for the return value is a single number."""

    def __init__(self, *args, **kwargs):
        super(Sql, self).__init__(*args, **kwargs)
        self.logger.debug("Init Sql")

    def define_sub_options(self):
        super(Sql, self).define_sub_options()
        self.sql_parser = self.subparsers.add_parser('sql',
                                                     help='Run sql/SP.',
                                                     description='Options\
                                                     for sql/SP.')
        self.sql_parser.add_argument('-s', '--sql',
                                     action='append',
                                     type=str,
                                     required=True,
                                     help='The sql or store procedure.',
                                     dest='sql')
        self.sql_parser.add_argument('-w', '--warning',
                                     default=0,
                                     type=int,
                                     required=False,
                                     help='Warning value for sql, default is %(default)s',
                                     dest='warning')
        self.sql_parser.add_argument('-c', '--critical',
                                     default=0,
                                     type=int,
                                     required=False,
                                     help='Critical value for sql, default is %(default)s',
                                     dest='critical')
        self.sql_parser.add_argument('--as_dict',
                                     default=pymysql.cursors.SSCursor,
                                     required=False,
                                     help='Set the return mode.',
                                     dest='as_dict')

    def sql_handle(self):
        self.__results = self.query(self.args.sql)
        self.close()
        if not self.__results:
            self.unknown("SP/SQL return nothing.")
        self.logger.debug("results: {}".format(self.__results))
        if len(self.__results) != 1:
            self.unknown("SP/SQL return more than one number.")
        self.__result = self.__results[0][0]
        if not isinstance(self.__result, (int, long)):
            self.unknown("SP/SQL not return a single number.")
        self.logger.debug("result: {}".format(self.__result))
        status = self.ok

        # Compare the vlaue.
        if self.__result > self.args.warning:
            status = self.warning
        if self.__result > self.args.critical:
            status = self.critical

        # Output
        self.shortoutput = "The result is {}".format(self.__result)
        self.longoutput.append("-------------------------------\n")
        self.longoutput.append(str(self.__results))
        self.longoutput.append("-------------------------------\n")
        self.perfdata.append("\n{sql}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=self.__result,
            sql=self.args.sql))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class Pool(Sql):

    """Register your own class here."""

    def __init__(self, *args, **kwargs):
        super(Pool, self).__init__(*args, **kwargs)


def main():
    """Register your own mode and handle method here."""
    plugin = Pool()
    arguments = sys.argv[1:]
    if 'sql' in arguments:
        plugin.sql_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
