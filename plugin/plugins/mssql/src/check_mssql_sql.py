#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""Copyright (C) Faurecia <http://www.faurecia.com/>.

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
import re
import logging
import argparse
import pickle
import pymssql


class Nagios(object):

    """Basic class for nagios."""

    def __init__(self, name=None, version='6.2.0', description='For MSSQL'):
        self._name = os.path.basename(sys.argv[0]) if not name else name
        self.__version = version
        self.__description = description

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("mssql")
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
        self.parser = argparse.ArgumentParser(description="Plugin for MSSQL.")
        self.parser.add_argument('-V', '--version',
                                 action='version',
                                 version='%s %s' % (self._name,
                                                    self.__version),
                                 help='Show version')
        self.parser.add_argument('-D', '--debug',
                                 action='store_true',
                                 required=False,
                                 help='Show debug informations.',
                                 dest='debug')

    def define_sub_options(self):
        self.mssql_parser = self.parser.add_argument_group('Mssql options',
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


# Extension for function monitoring.
# Just use the API from class Nagios and Mssql.


class Sql(Mssql):

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
                                     help='Warning value for sql',
                                     dest='warning')
        self.sql_parser.add_argument('-c', '--critical',
                                     default=0,
                                     type=int,
                                     required=False,
                                     help='Critical value for sql',
                                     dest='critical')
        self.sql_parser.add_argument('--as_dict',
                                     default=False,
                                     type=bool,
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


class Ijcore(Mssql):

    """Count the return value and show the lines.

    Monitoring Ijcore function.

    Replace Ijcore.

    """

    def __init__(self, *args, **kwargs):
        super(Ijcore, self).__init__(*args, **kwargs)
        self.logger.debug("Init ijcore")

    def define_sub_options(self):
        super(Ijcore, self).define_sub_options()
        self.ijcore_parser = self.subparsers.add_parser('ijcore',
                                                        help='For ijcore db',
                                                        description='Options\
                                                        for ijcore.')
        self.ijcore_parser.add_argument('-s', '--sql',
                                        required=True,
                                        help='String, use , to separate.',
                                        dest='sql')
        self.ijcore_parser.add_argument('-w', '--warning',
                                        default=0,
                                        type=int,
                                        required=False,
                                        help='Warning value for sql',
                                        dest='warning')
        self.ijcore_parser.add_argument('-c', '--critical',
                                        default=0,
                                        type=int,
                                        required=False,
                                        help='Critical value for sql',
                                        dest='critical')
        self.ijcore_parser.add_argument('--as_dict',
                                        default=True,
                                        type=bool,
                                        required=False,
                                        help='Set the return mode.',
                                        dest='as_dict')

    def ijcore_handle(self):
        # Init pickle data.
        if os.environ.get("NAGIOSENV"):
            self._picklefile_path = '/var/tmp/plugin/{NAGIOSENV}'.format(
                **os.environ)
        else:
            self._picklefile_path = '/var/tmp/plugin'
        try:
            if not os.path.isdir(self._picklefile_path):
                os.makedirs(self._picklefile_path)
        except OSError:
            self.unknown("Unable to create the retention folder\
                         {0._picklefile_path}".format(self))
        self._picklefile_name = self._name + "_" + self.args.server
        self._picklefile_pattern = 'p'

        self.sql = 'SELECT COUNT(*) AS number FROM [IJCore].[dbo].[dataCalloff] WHERE configurationCalloffStatusNumber=%d'
        self.sql0 = """
        DECLARE @id_list varchar(1000)
        DECLARE @sql varchar(8000)
        SET @id_list=%s
        SET @sql='SELECT COUNT(*) AS number FROM [IJCore].[dbo].[dataProcessLog] WHERE configurationLogID IN('+@id_list+') AND dataProcessLogID > %d'
        EXEC(@sql)
        """
        self.sql1 = 'SELECT [dataCalloffID],[configurationCalloffStatusNumber],[parameterCustomerAssemblyLineID],[dataCalloffJITOrder],[dataCalloffEngineSequence],[dataCalloffRequestPoint],[dataCalloffChassis],[dataCalloffAssemblySequence] FROM [IJCore].[dbo].[dataCalloff] WHERE configurationCalloffStatusNumber=%d order by [dataCalloffID] desc'
        self.sql2 = """
        DECLARE @id_list varchar(1000)
        DECLARE @sql varchar(8000)
        SET @id_list=%s
        SET @sql='SELECT [dataProcessLogCreationDate],[dataProcessLogID],[configurationLogID],[dataProcessLogParam1],[dataProcessLogParam2],[dataProcessLogParam3] FROM [IJCore].[dbo].[dataProcessLog] WHERE configurationLogID IN('+@id_list+') AND dataProcessLogID > %d order by [dataProcessLogID] desc'
        EXEC(@sql)
        """
        self.sql3 = """
        DECLARE @id_list varchar(1000)
        DECLARE @sql varchar(8000)
        SET @id_list=%s
        SET @sql='SELECT TOP 1 [dataProcessLogCreationDate],[dataProcessLogID],[configurationLogID],[dataProcessLogParam1],[dataProcessLogParam2],[dataProcessLogParam3] FROM [IJCore].[dbo].[dataProcessLog] WHERE configurationLogID IN('+@id_list+') order by [dataProcessLogID] desc'
        EXEC(@sql)
        """

        # Init the status
        status = self.ok

        # Just for sequence jump(7,90).
        if '90' == self.args.sql:
            self.shortoutput = "No new sequence jump error found in dataCalloff table."
            self.lines = self.query(self.sql % 90)
            self.logger.debug("lines: {}".format(self.lines))
            self.line = int(self.lines[0].get('number'))
            self.logger.debug("Sql return {} lines".format(self.line))
            if self.line > 200:
                status = self.critical
                self.shortoutput = "Found {} new sequence jump errors, Please check the Database.".format(self.line)
                self.__write_perfdata(self.line)
            else:
                self.results = self.query(self.sql1 % 90)
                self.close()
                self.logger.debug("results: {}".format(self.results))
                self.result = int(len(self.results))
                self.logger.debug("result: {}".format(self.result))
                # Compare the vlaue.
                if self.result > self.args.warning:
                    status = self.warning
                if self.result > self.args.critical:
                    status = self.critical
                # output for configurationCalloffStatus=90(configurationLogID=7)
                if self.result:
                    self.__write_perfdata(self.result)
                    self.shortoutput = "Found {} sequence jump error.".format(
                        self.result)
                    self.longoutput.append("-------------------------\n")
                    if isinstance(self.results[0], dict):
                        keys = self.results[0].keys()
                        for loop in range(0, self.result):
                            for key in keys:
                                value = str(self.results[loop].get(key)).strip("\n")
                                line = key + ": " + value
                                self.longoutput.append(line + "\n")
                            self.longoutput.append("-------------------------\n")

        # For other 14 alerts.
        elif ('90' not in self.args.sql) and (len(self.args.sql) > 0):
            self.shortoutput = "No new entry found in errorlog table."
            # Init information file.
            self.ijcore_file = ""
            self.__ijcore_file = '/var/tmp/plugin/ijcore/data/ijcore_' + self.args.server + '.txt'
            self.__common_file = '/var/tmp/plugin/ijcore/data/ijcore.txt'
            if os.path.isfile(self.__ijcore_file):
                self.ijcore_file = self.__ijcore_file
            elif os.path.isfile(self.__common_file):
                self.ijcore_file = self.__common_file
            else:
                self.unknown("{} file not exist.".format(self.ijcore_file))
            self.logger.debug(">>> ijcore_file: {}".format(self.ijcore_file))
            # Get the pickfile
            self.picklefile_extend = 'ijcore'
            self.picklefile = '{0}/{1}_{2}_{3}.pkl'.format(
                self._picklefile_path,
                self._picklefile_name,
                self.picklefile_extend,
                self._picklefile_pattern)
            self.logger.debug(">>> picklefile: {}".format(self.picklefile))
            # Get self.old_id
            if not os.path.isfile(self.picklefile):
                self.old_id = 0
            else:
                self.old_id = int(self.__load_id(self.picklefile))
            self.logger.debug("old id is {}".format(self.old_id))
            # Get the self.lines
            self.lines = self.query(self.sql0 % (self.args.sql, self.old_id))
            self.line = int(self.lines[0].get('number'))
            self.logger.debug("Sql return {} lines".format(self.line))
            # Write the last Id to temp file.
            self.tops = self.query(self.sql3 % self.args.sql)
            self.logger.debug("tops: {}".format(self.tops))
            if self.tops:
                self.top = int(self.tops[0].get('dataProcessLogID'))
            else:
                self.top = 0
            self.logger.debug("top number {}".format(self.top))
            self.__dump_id(self.top, self.picklefile)
            # Compare the line
            if self.line > 200:
                status = self.critical
                self.shortoutput = "Found {} new errorlog entry, Please check the database.".format(self.line)
                self.__write_perfdata(self.line)
            else:
                self.results = self.query(self.sql2 % (self.args.sql, self.old_id))
                self.logger.debug("results: {}".format(self.results))
                self.result = int(len(self.results))
                self.logger.debug("result: {}".format(self.result))
                self.__write_perfdata(self.result)
                if not self.result:
                    if self.top < self.old_id:
                        status = self.warning
                        self.shortoutput = "Data was delete, Please force check."
                else:
                    status = self.critical
                    self.__write_shortoutput(self.results)
                    self.__write_longoutput(self.results)

        # Useless arguments.
        else:
            self.unknown("Useless arguments for -s.")

        # Close the connection
        self.close()

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")

    def __dump_id(self, obj, filename):
        """Write something to the pickfile."""
        try:
            fw = open(filename, 'wb')
            pickle.dump(obj, fw)
            fw.close()
        except Exception as e:
            self.unknown("dump_id error: {}".format(e))

    def __load_id(self, filename):
        """Read something from the pickfile."""
        try:
            fr = open(filename, 'rb')
            obj = pickle.load(fr)
            fr.close()
            return obj
        except Exception as e:
            self.__dump_id(0, filename)
            self.unknown("load_id error, please force check: {}".format(e))

    def __read_file(self, filename):
        try:
            handle = open(filename, 'r')
            lines = handle.readlines()
            handle.close()
            return lines
        except Exception as e:
            self.unknown("read_file error, please check {}.").format(e)

    def __write_shortoutput(self, results):
        """Get the shortoutput when it's critical."""
        file_list = self.__read_file(self.ijcore_file)
        short_list = []
        short_list.append("Found {} new entry in errorlog table".format(int(len(results))))
        for loop in range(0, len(results)):
            time = results[loop].get("dataProcessLogCreationDate")
            cid = results[loop].get("configurationLogID")
            id = results[loop].get("dataProcessLogID")
            param1 = results[loop].get("dataProcessLogParam1")
            param2 = results[loop].get("dataProcessLogParam2")
            param3 = results[loop].get("dataProcessLogParam3")
            for line in file_list:
                if cid == int(line.split()[0]):
                    code = line.split()[1]
                    self.logger.debug("code: {}".format(code))
                    comment = str(line.split('|')[1]).strip("\n")
                    self.logger.debug("comment: {}".format(comment))
                    display = str(comment.replace("$configurationLogID", str(cid)))
                    display = str(display.replace("$configurationLogCode", code))
                    display = str(display.replace("$dataProcessLogCreationDate", str(time)))
                    display = str(display.replace("$dataProcessLogID", str(id)))
                    display = str(display.replace("$dataProcessLogParam1", param1))
                    display = str(display.replace("$dataProcessLogParam2", param2))
                    display = str(display.replace("$dataProcessLogParam3", param3))
            short_list.append(" , " + display)
        self.shortoutput = "".join(short_list)

    def __longoutput_sort(self, yourkey, results, loop):
        keys = results[loop].keys()
        for key in keys:
            if key == yourkey:
                value = str(results[loop].get(key)).strip()
                line = key + ": " + value
                self.longoutput.append(line)

    def __write_longoutput(self, results):
        if isinstance(results[0], dict):
            for loop in range(0, len(results)):
                self.longoutput.append("\n")
                self.__longoutput_sort("dataProcessLogCreationDate", results, loop)
                self.__longoutput_sort("configurationLogID", results, loop)
                self.__longoutput_sort("dataProcessLogID", results, loop)
                self.__longoutput_sort("dataProcessLogParam1", results, loop)
                self.__longoutput_sort("dataProcessLogParam2", results, loop)
                self.__longoutput_sort("dataProcessLogParam3", results, loop)

    def __write_perfdata(self, line):
        self.perfdata.append("\n{sql}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=line,
            sql=self.args.sql))


class DatabaseUsed(Mssql):

    """For check the database-size, database-used, database-percent."""

    def __init__(self, *args, **kwargs):
        super(DatabaseUsed, self).__init__(*args, **kwargs)
        self.logger.debug("Init databaseused")

    def define_sub_options(self):
        super(DatabaseUsed, self).define_sub_options()
        self.du_parser = self.subparsers.add_parser('database-used',
                                                    help='For\
                                                    database-used.',
                                                    description='Options\
                                                    for database-used.')
        self.du_parser.add_argument('-w', '--warning',
                                    default=0,
                                    type=float,
                                    required=False,
                                    help='Warning value for data file. if mode\
                                    dbpercent, 90 means 0.9.',
                                    dest='warning')
        self.du_parser.add_argument('-c', '--critical',
                                    default=0,
                                    type=float,
                                    required=False,
                                    help='Critical value for data file.',
                                    dest='critical')
        self.du_parser.add_argument('-m', '--mode',
                                    default='dbused',
                                    required=False,
                                    help='Choice from dbused dbsize dbpercent.',
                                    dest='mode')
        self.du_parser.add_argument('-r', '--regex',
                                    required=False,
                                    help='Specify the DB you want. Use regex.',
                                    dest='regex')
        self.du_parser.add_argument('--as_dict',
                                    default=True,
                                    type=bool,
                                    required=False,
                                    help='Set the return mode.',
                                    dest='as_dict')

    def database_used_handle(self):
        self.database_used_sql = """
SET  NOCOUNT ON;
SET  ANSI_NULLS ON;
SET  QUOTED_IDENTIFIER ON;

DECLARE
  @SQL     NVARCHAR(4000),
  @dbname  sysname;

declare
  @datatab table
          (name    sysname,
           dbsize  float,
           dbused  float,
           logsize float,
           logused float);

declare
  dbcursor      cursor for
                select name from sys.databases order by database_id;

open dbcursor;
fetch NEXT FROM dbcursor INTO @dbname;

while @@FETCH_STATUS = 0
BEGIN
  set @SQL='use ' + quotename(@dbname) + '; SELECT ''' +  @dbname + ''' as dbname' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (0, 2, 4)) dbsize' +
       ', SUM(CAST(a.total_pages AS FLOAT)) / 128 reservedsize' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (1, 3)) logsize' +
       ', (select sum(cast(fileproperty(name, ''SpaceUsed'') as float))/128 from sys.database_files where type in (1,3)) logUsedMB' +
       ' FROM ' + quotename(@dbname) + '.sys.partitions p' +
       ' INNER JOIN ' + quotename(@dbname) + '.sys.allocation_units a ON p.partition_id = a.container_id' +
       ' LEFT OUTER JOIN ' + quotename(@dbname) + '.sys.internal_tables it ON p.object_id = it.object_id';

  insert into @datatab
  execute(@SQL);
  --print @SQL
  fetch NEXT FROM dbcursor INTO @dbname;
end;

CLOSE dbcursor;
DEALLOCATE dbcursor;

select  name
      , dbsize
      , dbused
      , round(dbused / dbsize *100, 2) dbpercent
from @datatab d order by name;
"""
        self.__dbwarn = []
        self.__dbwarn_rest = []
        self.__dbcrit = []
        self.__dbcrit_rest = []
        self.__new_results = []

        self.__results = self.query(self.database_used_sql)
        self.close()
        self.logger.debug("results: {}".format(self.__results))

        # filter.
        if self.args.regex:
            for loop in range(0, len(self.__results)):
                self.logger.debug("line_dict {0}: {1}".format(
                    loop, self.__results[loop]))
                name = str(self.__results[loop]['name'])
                if re.findall(self.args.regex, name):
                    self.__new_results.append(self.__results[loop])
        else:
            self.__new_results = self.__results

        status = self.ok
        self.__result = []
        self.__result_rest = self.__new_results

        for loop in range(0, len(self.__new_results)):
            line_dict = self.__new_results[loop]
            mode = float(line_dict[self.args.mode])
            self.logger.debug("mode: {}".format(mode))

            # Compare the db
            if self.args.warning:
                if mode > self.args.warning:
                    self.__dbwarn.append(line_dict)
                else:
                    self.__dbwarn_rest.append(line_dict)
            if self.args.critical:
                if mode > self.args.critical:
                    self.__dbcrit.append(line_dict)
                else:
                    self.__dbcrit_rest.append(line_dict)

        # get status and results.
        if len(self.__dbwarn):
            status = self.warning
            self.__result = self.__dbwarn
            self.__result_rest = self.__dbwarn_rest
        if len(self.__dbcrit):
            status = self.critical
            self.__result = self.__dbcrit
            self.__result_rest = self.__dbcrit_rest

        # Output for nagios
        self.shortoutput = "{0} db, {1} db warning, {2} db critical.".format(
            len(self.__new_results), len(self.__dbwarn), len(self.__dbcrit))
        self.longoutput.append("---------------------------------\n")
        self.__write_longoutput(self.__result)
        self.longoutput.append("=============== OK ===============\n")
        self.__write_longoutput(self.__result_rest)
        self.perfdata.append("\nError number={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=len(self.__result)))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")

    def __write_longoutput(self, result):
        try:
            if result:
                if isinstance(result[0], dict):
                    keys = result[0].keys()
                    for loop in range(0, len(result)):
                        for key in keys:
                            value = str(result[loop].get(key)).strip("\n")
                            if key == 'dbpercent':
                                unit = "%"
                            elif key == 'dbsize':
                                unit = "MB"
                            elif key == 'dbused':
                                unit = "MB"
                            else:
                                unit = ""
                            line = key + ": " + value + unit
                            self.longoutput.append(line + "\n")
                        self.longoutput.append("---------------------------\n")
        except Exception as e:
            self.unknown("database-used write_longoutput error: {}".format(e))


class DatabaseLogUsed(Mssql):

    """For check database-log-size, database-log-used, database-log-percent."""

    def __init__(self, *args, **kwargs):
        super(DatabaseLogUsed, self).__init__(*args, **kwargs)
        self.logger.debug("Init databaselogused")

    def define_sub_options(self):
        super(DatabaseLogUsed, self).define_sub_options()
        self.dl_parser = self.subparsers.add_parser('databaselog-used',
                                                    help='For\
                                                    databaselog-used.',
                                                    description='Options\
                                                    for databaselog-used.')
        self.dl_parser.add_argument('-w', '--warning',
                                    default=0,
                                    type=float,
                                    required=False,
                                    help='Warning value for log file.',
                                    dest='warning')
        self.dl_parser.add_argument('-c', '--critical',
                                    default=0,
                                    type=float,
                                    required=False,
                                    help='Critical value for log file.',
                                    dest='critical')
        self.dl_parser.add_argument('-m', '--mode',
                                    default='logused',
                                    required=False,
                                    help='Choose from logused logsize logpercent',
                                    dest='mode')
        self.dl_parser.add_argument('-r', '--regex',
                                    required=False,
                                    help='Specify the DB you want.',
                                    dest='regex')
        self.dl_parser.add_argument('--as_dict',
                                    default=True,
                                    type=bool,
                                    required=False,
                                    help='Set the return mode.',
                                    dest='as_dict')

    def database_log_used_handle(self):
        self.databaselog_used_sql = """
SET  NOCOUNT ON;
SET  ANSI_NULLS ON;
SET  QUOTED_IDENTIFIER ON;

DECLARE
  @SQL     NVARCHAR(4000),
  @dbname  sysname;

declare
  @datatab table
          (name    sysname,
           dbsize  float,
           dbused  float,
           logsize float,
           logused float);

declare
  dbcursor      cursor for
                select name from sys.databases order by database_id;

open dbcursor;
fetch NEXT FROM dbcursor INTO @dbname;

while @@FETCH_STATUS = 0
BEGIN
  set @SQL='use ' + quotename(@dbname) + '; SELECT ''' +  @dbname + ''' as dbname' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (0, 2, 4)) dbsize' +
       ', SUM(CAST(a.total_pages AS FLOAT)) / 128 reservedsize' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (1, 3)) logsize' +
       ', (select sum(cast(fileproperty(name, ''SpaceUsed'') as float))/128 from sys.database_files where type in (1,3)) logUsedMB' +
       ' FROM ' + quotename(@dbname) + '.sys.partitions p' +
       ' INNER JOIN ' + quotename(@dbname) + '.sys.allocation_units a ON p.partition_id = a.container_id' +
       ' LEFT OUTER JOIN ' + quotename(@dbname) + '.sys.internal_tables it ON p.object_id = it.object_id';

  insert into @datatab
  execute(@SQL);
  --print @SQL
  fetch NEXT FROM dbcursor INTO @dbname;
end;

CLOSE dbcursor;
DEALLOCATE dbcursor;

select  name
      , logsize
      , logused
      ,round(logused / logsize *100, 2) logpercent
from @datatab d order by name;
"""
        self.__logwarn = []
        self.__logwarn_rest = []
        self.__logcrit = []
        self.__logcrit_rest = []
        self.__new_results = []

        self.__results = self.query(self.databaselog_used_sql)
        self.close()
        self.logger.debug("results: {}".format(self.__results))

        # filter
        if self.args.regex:
            for loop in range(0, len(self.__results)):
                self.logger.debug("line_dict {0}: {1}".format(
                    loop, self.__results[loop]))
                name = str(self.__results[loop]['name'])
                if re.findall(self.args.regex, name):
                    self.__new_results.append(self.__results[loop])
        else:
            self.__new_results = self.__results

        status = self.ok
        self.__result = []
        self.__result_rest = self.__new_results

        for loop in range(0, len(self.__new_results)):
            line_dict = self.__new_results[loop]
            mode = float(line_dict[self.args.mode])

            # Compare the db
            if self.args.warning:
                if mode > self.args.warning:
                    self.__logwarn.append(line_dict)
                else:
                    self.__logwarn_rest.append(line_dict)
            if self.args.critical:
                if mode > self.args.critical:
                    self.__logcrit.append(line_dict)
                else:
                    self.__logcrit_rest.append(line_dict)

        # get status and result.
        if len(self.__logwarn):
            status = self.warning
            self.__result = self.__logwarn
            self.__result_rest = self.__logwarn_rest
        if len(self.__logcrit):
            status = self.critical
            self.__result = self.__logcrit
            self.__result_rest = self.__logcrit_rest

        # Output for nagios
        self.shortoutput = "{0} dblog, {1} warning, {2} critical.".format(
            len(self.__new_results), len(self.__logwarn), len(self.__logcrit))
        self.longoutput.append("---------------------------------\n")
        self.__write_longoutput(self.__result)
        self.longoutput.append("=============== OK ===============\n")
        self.__write_longoutput(self.__result_rest)
        self.perfdata.append("\nError number={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=len(self.__result)))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")

    def __write_longoutput(self, result):
        try:
            if result:
                if isinstance(result[0], dict):
                    keys = result[0].keys()
                    for loop in range(0, len(result)):
                        for key in keys:
                            value = str(result[loop].get(key)).strip("\n")
                            if key == 'logpercent':
                                unit = "%"
                            elif key == 'logsize':
                                unit = "MB"
                            elif key == 'logused':
                                unit = "MB"
                            else:
                                unit = ""
                            line = key + ": " + value + unit
                            self.longoutput.append(line + "\n")
                        self.longoutput.append("---------------------------\n")
        except Exception as e:
            self.unknown("databaselog-used write_longoutput error: {}".format(
                e))


class Diff(Sql, Esupply, Ijcore, DatabaseUsed, DatabaseLogUsed):

    """Summary all function monitoring class."""

    def __init__(self, *args, **kwargs):
        super(Diff, self).__init__(*args, **kwargs)


def main():
    plugin = Diff()
    arguments = sys.argv[1:]
    if 'sql' in arguments:
        plugin.sql_handle()
    elif 'esupply' in arguments:
        plugin.esupply_handle()
    elif 'ijcore' in arguments:
        plugin.ijcore_handle()
    elif 'database-used' in arguments:
        plugin.database_used_handle()
    elif 'databaselog-used' in arguments:
        plugin.database_log_used_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
