#!/usr/bin/env python
# -*- coding: utf-8 -*-
######################################################################
# Copyright (C) 2015 Faurecia (China) Holding Co.,Ltd.               #
# All rights reserved                                                #
# Name: check_mssql_sql.py
# Author: Canux canuxcheng@gmail.com                                 #
# Version: V1.0                                                      #
# Time: Mon 07 Mar 2016 02:46:39 AM EST
######################################################################
# Description:
######################################################################

import os
import sys
import logging
import argparse
import pymssql


class Base(object):
    """Basic class for everything."""
    def __init__(self, name=None, version='1.0.0', description='For MSSQL'):
        self.name = os.path.basename(sys.argv[0]) if not name else name

        # Init output data.
        self._output = ""
        self.shortoutput = ""
        self.longoutput = []
        self.perfdata = []

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("mssql")
        self.logger.setLevel(logging.INFO)

        # Init  the argument
        self.__define_options()
        self.define_sub_options()
        self.__parse_options()

        if self.args.debug:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug("===== BEGIN DEBUG =====")
        self.logger.debug("Init base")

        if self.__class__.__name__ == "Base":
            self.logger.debug("===== END DEBUG =====")

    def __define_options(self):
        self.parser = argparse.ArgumentParser(description="Plugin for MSSQL.")
        self.parser.add_argument('-V', '--version',
                                 action='version',
                                 version='%s %s" % (self.name, self.version)',
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


class Mssql(Base):
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
        return self.results

    def close(self):
        """Close the connection."""
        try:
            self.conn.close()
            self.logger.debug("Close ok")
        except pymssql.Error as e:
            self.unknown("Close connect error: %s" % e)

    def version(self):
        self.results = self.query("select @@version as version")
        self.logger.debug("MSSQL Version: {}".format(self.results))

    def define_sub_options(self):
        super(Mssql, self).define_sub_options()
        self.mssql_parser.add_argument('-H', '--server',
                                       required=True,
                                       help='database server.',
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
                                       help='database name.',
                                       dest='database')
        self.mssql_parser.add_argument('-t', '--timeout',
                                       default=15,
                                       type=int,
                                       required=False,
                                       help='query timeout.',
                                       dest='timeout')
        self.mssql_parser.add_argument('-l', '--login_timeout',
                                       default=30,
                                       type=int,
                                       required=False,
                                       help='connection and login time out.',
                                       dest='login_timeout')
        self.mssql_parser.add_argument('-c', '--charset',
                                       default='utf8',
                                       type=str,
                                       required=False,
                                       help='set the charset.',
                                       dest='charset')


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
        self.version()
        self.results = self.query(self.args.sql)
        self.close()
        if not self.results:
            self.unknown("SP/SQL return nothing.")
        self.logger.debug("results: {}".format(self.results))
        if len(self.results) != 1:
            self.unknown("SP/SQL return more than one number.")
        self.result = self.results[0][0]
        if not isinstance(self.result, (int, long)):
            self.unknown("SP/SQL not return a single number.")
        self.logger.debug("result: {}".format(self.result))
        status = self.ok

        # Compare the vlaue.
        if self.result > self.args.warning:
            status = self.warning
        if self.result > self.args.critical:
            status = self.critical

        # Output
        self.shortoutput = "The result is {}".format(self.result)
        self.longoutput.append("-------------------------------\n")
        self.longoutput.append(str(self.results))
        self.longoutput.append("-------------------------------\n")
        self.perfdata.append("\n{sql}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=self.result,
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
        self.version()
        self.results = self.query(self.args.sql)
        self.close()
        self.logger.debug("results: {}".format(self.results))
        self.result = int(len(self.results))
        self.logger.debug("result: {}".format(self.result))
        status = self.ok

        # Compare the vlaue.
        if self.result > self.args.warning:
            status = self.warning
        if self.result > self.args.critical:
            status = self.critical

        # Output for nagios
        self.shortoutput = "The result is {}".format(self.result)
        self.longoutput.append("-------------------------------\n")
        if self.result:
            if isinstance(self.results[0], dict):
                keys = self.results[0].keys()
                for loop in range(0, self.result):
                    for key in keys:
                        value = str(self.results[loop].get(key)).strip("\n")
                        line = key + ": " + value
                        self.longoutput.append(line + "\n")
                    self.longoutput.append("-------------------------------\n")
        self.perfdata.append("\n{sql}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=self.result,
            sql=self.args.sql))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class IjcoreM(Mssql):
    """Count the return value and show the lines.
    Monitoring Ijcore process.
    Replace IjcoreM.
    """
    def __init__(self, *args, **kwargs):
        super(IjcoreM, self).__init__(*args, **kwargs)
        self.logger.debug("Init ijcorem")

    def define_sub_options(self):
        super(IjcoreM, self).define_sub_options()
        self.ijcorem_parser = self.subparsers.add_parser('ijcorem',
                                                         help='For ijcore db',
                                                         description='Options\
                                                         for ijcore.')
        self.ijcorem_parser.add_argument('-s', '--sql',
                                         action='append',
                                         type=str,
                                         required=True,
                                         help='The sql or store procedure.',
                                         dest='sql')
        self.ijcorem_parser.add_argument('-w', '--warning',
                                         default=0,
                                         type=int,
                                         required=False,
                                         help='Warning value for sql',
                                         dest='warning')
        self.ijcorem_parser.add_argument('-c', '--critical',
                                         default=0,
                                         type=int,
                                         required=False,
                                         help='Critical value for sql',
                                         dest='critical')
        self.ijcorem_parser.add_argument('--as_dict',
                                         default=True,
                                         type=bool,
                                         required=False,
                                         help='Set the return mode.',
                                         dest='as_dict')

    def ijcorem_handle(self):
        self.version()
        self.results = self.query(self.args.sql)
        self.close()
        self.logger.debug("results: {}".format(self.results))
        self.result = int(len(self.results))
        self.logger.debug("result: {}".format(self.result))
        status = self.ok

        # Compare the vlaue.
        if self.result > self.args.warning:
            status = self.warning
        if self.result > self.args.critical:
            status = self.critical

        # Output for nagios
        self.shortoutput = "The result is {}".format(self.result)
        self.longoutput.append("-------------------------------\n")
        if self.result:
            if isinstance(self.results[0], dict):
                keys = self.results[0].keys()
                for loop in range(0, self.result):
                    for key in keys:
                        value = str(self.results[loop].get(key)).strip("\n")
                        line = key + ": " + value
                        self.longoutput.append(line + "\n")
                    self.longoutput.append("-------------------------------\n")
        self.perfdata.append("\n{sql}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=self.result,
            sql=self.args.sql))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class DatabaseUsed(Mssql):
    """For check the database-size, database-used, database-percent.
    """
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
                                    default=80,
                                    type=int,
                                    required=False,
                                    help='Warning value for data file.',
                                    dest='warning')
        self.du_parser.add_argument('-c', '--critical',
                                    default=90,
                                    type=int,
                                    required=False,
                                    help='Critical value for data file.',
                                    dest='critical')
        self.du_parser.add_argument('--regex',
                                    action='append',
                                    required=False,
                                    help='Specify the DB you want.',
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
  DBCursor      cursor for
                select name from sys.databases order by database_id;

open dbcursor;
fetch NEXT FROM dbcursor INTO @dbname;

while @@FETCH_STATUS = 0
BEGIN
  set @SQL='use ' + @dbname + '; SELECT ''' +  @dbname + ''' as dbname' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (0, 2, 4)) dbsize' +
       ', SUM(CAST(a.total_pages AS FLOAT)) / 128 reservedsize' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (1, 3)) logsize' +
       ', (select sum(cast(fileproperty(name, ''SpaceUsed'') as float))/128 from sys.database_files where type in (1,3)) logUsedMB' +
       ' FROM ' + @dbname + '.sys.partitions p' +
       ' INNER JOIN ' + @dbname + '.sys.allocation_units a ON p.partition_id = a.container_id' +
       ' LEFT OUTER JOIN ' + @dbname + '.sys.internal_tables it ON p.object_id = it.object_id';

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
        self.dbwarn = []
        self.dbcrit = []
        self.result = []
        self.version()
        self.results = self.query(self.database_used_sql)
        self.close()
        self.logger.debug("results: {}".format(self.results))
        status = self.ok

        for loop in range(0, len(self.results)):
            self.line_dict = self.results[loop]
            self.logger.debug("line_dict {0}: {1}".format(loop,
                                                          self.line_dict))
            self.dbpect = float(self.line_dict['dbpercent'])

            # Compare the db
            if self.dbpect > self.args.warning:
                self.dbwarn.append(self.line_dict)
            if self.dbpect > self.args.critical:
                self.dbcrit.append(self.line_dict)

        if len(self.dbwarn):
            self.status = self.warning
            self.result = self.dbwarn
        if len(self.dbcrit):
            status = self.critical
            self.result = self.dbcrit

        # Output for nagios
        self.shortoutput = "{0} db, {1} db warning, {2} db critical.".format(
            len(self.results), len(self.dbwarn), len(self.dbcrit))
        self.longoutput.append("-------------------------------\n")
        if self.result:
            if isinstance(self.result[0], dict):
                keys = self.result[0].keys()
                for loop in range(0, len(self.result)):
                    for key in keys:
                        value = str(self.result[loop].get(key)).strip("\n")
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
                    self.longoutput.append("-------------------------------\n")
        self.perfdata.append("\nError number={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=len(self.result)))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class DatabaseLogUsed(Mssql):
    """For check database-log-size, database-log-used, database-log-percent.
    """
    def __init__(self, *args, **kwargs):
        super(DatabaseLogUsed, self).__init__(*args, **kwargs)
        self.logger.debug("Init databaseused")

    def define_sub_options(self):
        super(DatabaseLogUsed, self).define_sub_options()
        self.dl_parser = self.subparsers.add_parser('databaselog-used',
                                                    help='For\
                                                    databaselog-used.',
                                                    description='Options\
                                                    for databaselog-used.')
        self.dl_parser.add_argument('-w', '--warning',
                                    default=80,
                                    type=int,
                                    required=False,
                                    help='Warning value for log file.',
                                    dest='warning')
        self.dl_parser.add_argument('-c', '--critical',
                                    default=90,
                                    type=int,
                                    required=False,
                                    help='Critical value for log file.',
                                    dest='critical')
        self.dl_parser.add_argument('--regex',
                                    action='append',
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
          logsize  float,
          logused  float);

declare
  DBCursor      cursor for
                select name from sys.databases order by database_id;

open dbcursor;
fetch NEXT FROM dbcursor INTO @dbname;

while @@FETCH_STATUS = 0
BEGIN
  set @SQL='use ' + @dbname + '; SELECT ''' +  @dbname + ''' as dbname' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (0, 2, 4)) dbsize' +
       ', SUM(CAST(a.total_pages AS FLOAT)) / 128 reservedsize' +
       ', (SELECT SUM(CAST(size AS FLOAT)) / 128 FROM sys.database_files WHERE  type IN (1, 3)) logsize' +
       ', (select sum(cast(fileproperty(name, ''SpaceUsed'') as float))/128 from sys.database_files where type in (1,3)) logUsedMB' +
       ' FROM ' + @dbname + '.sys.partitions p' +
       ' INNER JOIN ' + @dbname + '.sys.allocation_units a ON p.partition_id = a.container_id' +
       ' LEFT OUTER JOIN ' + @dbname + '.sys.internal_tables it ON p.object_id = it.object_id';

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
      , round(logused / logsize *100, 2) logpercent
from @datatab d order by name;
"""
        self.logwarn = []
        self.logcrit = []
        self.log_result = []
        self.version()
        self.results = self.query(self.databaselog_used_sql)
        self.close()
        self.logger.debug("results: {}".format(self.results))
        status = self.ok

        for loop in range(0, len(self.results)):
            self.line_dict = self.results[loop]
            self.logger.debug("line_dict {0}: {1}".format(loop,
                                                          self.line_dict))
            self.logpect = float(self.line_dict['logpercent'])

            # Compare the db
            if self.logpect > self.args.warning:
                self.logwarn.append(self.line_dict)
            if self.logpect > self.args.critical:
                self.logcrit.append(self.line_dict)

        if len(self.logwarn):
            status = self.warning
            self.log_result = self.logwarn
        if len(self.logcrit):
            status = self.critical
            self.log_result = self.logcrit

        # Output for nagios
        self.shortoutput = "{0} db, {1} db warning, {2} db critical.".format(
            len(self.results), len(self.logwarn), len(self.logcrit))
        self.longoutput.append("-------------------------------\n")
        if self.log_result:
            if isinstance(self.log_result[0], dict):
                keys = self.log_result[0].keys()
                for loop in range(0, len(self.log_result)):
                    for key in keys:
                        value = str(self.log_result[loop].get(key)).strip("\n")
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
                    self.longoutput.append("-------------------------------\n")
        self.perfdata.append("\nError number={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=len(self.log_result)))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class Diff(Sql, Esupply, IjcoreM, DatabaseUsed, DatabaseLogUsed):
    def __init__(self, *args, **kwargs):
        super(Diff, self).__init__(*args, **kwargs)


def main():
    plugin = Diff()
    arguments = sys.argv[1:]
    if 'sql' in arguments:
        plugin.sql_handle()
    elif 'esupply' in arguments:
        plugin.esupply_handle()
    elif 'ijcorem' in arguments:
        plugin.ijcorem_handle()
    elif 'database-used' in arguments:
        plugin.database_used_handle()
    elif 'databaselog-used' in arguments:
        plugin.database_log_used_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
