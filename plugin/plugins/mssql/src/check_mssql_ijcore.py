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
import pickle
import pymssql


class Nagios(object):

    """Basic class for nagios."""

    def __init__(self, name=None, version='1.0.0.0', description='For IJCORE MSSQL'):
        self.__name = os.path.basename(sys.argv[0]) if not name else name
        self.__version = version
        self.__description = description

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("ijcore")
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
        self.parser = argparse.ArgumentParser(description="Plugin for IJCORE MSSQL.")
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
            self.logger.debug("close cursor ok")
        except pymssql.Error as e:
            self.unknown("Close cursor error: %s" % e)
        return self.results

    def close(self):
        """Close the connection."""
        try:
            self.conn.close()
            self.logger.debug("Close connect succeed")
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


class Ijcore(Mssql):

    """Use nagios to monitoring IJCore to replace ijcoreM."""

    def __init__(self, *args, **kwargs):
        super(Ijcore, self).__init__(*args, **kwargs)
        self.logger.debug("Init ijcore")

    def define_sub_options(self):
        super(Ijcore, self).define_sub_options()
        self.ijcore_parser = self.subparsers.add_parser('ijcore',
                                                        help='For ijcore db',
                                                        description='Options\
                                                        for ijcore.')
        self.ijcore_parser.add_argument('--localid',
                                        required=True,
                                        help='LocalID.',
                                        dest='localid')
        self.ijcore_parser.add_argument('--messagecolumn',
                                        required=True,
                                        help='MessageColumn',
                                        dest='messagecolumn')
        self.ijcore_parser.add_argument('--localtimecolumn',
                                        required=True,
                                        help='LocalTimeColumn',
                                        dest='localtimecolumn')
        self.ijcore_parser.add_argument('-t', '--table',
                                        required=True,
                                        help='Table name.',
                                        dest='table')
        self.ijcore_parser.add_argument('-w', '--where',
                                        required=True,
                                        help='Where condition.',
                                        dest='where')
        self.ijcore_parser.add_argument('-c', '--code',
                                        required=True,
                                        help='Unique ID for each alert on one ijcore server.',
                                        dest='code')
        self.ijcore_parser.add_argument('-m', '--message',
                                        default='No new entry fond.',
                                        required=True,
                                        help='The error type + name + message.',
                                        dest='message')
        self.ijcore_parser.add_argument('-n', '--number',
                                        default=100,
                                        type=int,
                                        required=False,
                                        help="The max number show in nagios dashboard. Default is %(default)s.",
                                        dest="number")
        self.ijcore_parser.add_argument('--as_dict',
                                        default=True,
                                        type=bool,
                                        required=False,
                                        help='Set the return mode.',
                                        dest='as_dict')

    def ijcore_handle(self):
        # Init pickle data.
        if os.environ.get("NAGIOSENV"):
            self.picklefile_path = '/var/tmp/plugin/{NAGIOSENV}'.format(**os.environ)
        else:
            self.picklefile_path = '/var/tmp/plugin'
        try:
            if not os.path.isdir(self.picklefile_path):
                os.makedirs(self.picklefile_path)
        except OSError:
            self.unknown("Unable to create the retention folder\
                         {0._picklefile_path}".format(self))
        self.picklefile_name = os.path.basename(sys.argv[0]) + "_" + self.args.server
        self.picklefile_code = self.args.code
        self.picklefile = '{0}/{1}_{2}.pkl'.format(
            self.picklefile_path,
            self.picklefile_name,
            self.picklefile_code)
        self.logger.debug(">>> picklefile: {}".format(self.picklefile))

        # Init the status
        status = self.ok
        self.shortoutput = "No new entry found."

        # Connect to Mssql and Run sql query, then close the connection.
        self.__sql = 'SELECT' + ' ' + self.args.localid +\
            ',' + self.args.messagecolumn +\
            ',' + self.args.localtimecolumn + ' ' +\
            'FROM' + ' ' + self.args.table + ' ' +\
            'WHERE' + ' ' + self.args.where
        self.__results = self.query(self.__sql)
        self.close()
        self.logger.debug("results: {}".format(self.__results))
        # [{u'dataProductionInternalOrderBarcode': u'B8SSILX162210019',
        # u'RepeatedBarcode': 2,
        # u'dateTime': datetime.datetime(2016, 12, 13, 7, 30, 4, 567000)}]

        # Check if the file exist.
        if not os.path.isfile(self.picklefile):
            self.__dump_id(self.__results, self.picklefile)
            self.unknown("This is the first time to run this plugin, please force check.")
        else:
            # Read old dump_list from temp file.
            self.dump_list = self.__load_id(self.picklefile)
            self.logger.debug("dump_list: {}".format(self.dump_list))
            # Write new self.__results in temp file.
            self.__dump_id(self.__results, self.picklefile)
            # Compare old dump_list and new self.__results.
            self.diff_list = self.__compare_id(self.__results, self.dump_list)
            self.logger.debug("diff_list: {}".format(self.diff_list))
            if self.diff_list:
                status = self.critical
                self.__write_longoutput(self.diff_list)
                self.shortoutput = self.args.message
            self.__write_perfdata(self.diff_list)

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")

    def __compare_id(self, new, old):
        """Compare the localid and return a different list."""
        self.diff_list = []
        old_localid_list = []
        [old_localid_list.append(old_dict.get(self.args.localid)) for old_dict in old]
        for new_dict in new:
            self.logger.debug("new_dict: {}".format(new_dict))
            new_localid = new_dict.get(self.args.localid)
            if new_localid not in old_localid_list:
                self.diff_list.append(new_dict)
        return self.diff_list

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
            self.unknown("load_id error: {}".format(e))

    def __write_longoutput(self, results):
        self.longoutput.append("--------------------------------------")
        if isinstance(results[0], dict):
            for loop in range(0, len(results)):
                keys = results[loop].keys()
                for key in keys:
                    value = str(results[loop].get(key)).strip()
                    line = key + ": " + value
                    self.longoutput.append(line)
                self.longoutput.append("--------------------------------------")

    def __write_perfdata(self, results):
        self.perfdata.append("\n{code}={result};{warn};{crit};0;".format(
            crit=0,
            warn=0,
            result=int(len(results)),
            code=self.args.code))


class Register(Ijcore):

    """Summary all function monitoring class."""

    def __init__(self, *args, **kwargs):
        super(Register, self).__init__(*args, **kwargs)


def main():
    plugin = Register()
    arguments = sys.argv[1:]
    if 'ijcore' in arguments:
        plugin.ijcore_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
