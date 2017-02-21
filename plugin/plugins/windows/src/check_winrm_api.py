#!/usr/bin/env python
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

import sys
import logging
import argparse

import winrm


class Monitor(object):

    """Basic class for monitor.

    Nagios and tools based on nagios have the same status.
    All tools have the same output except check_mk.

        Services Status:
        0 green  OK
        1 yellow Warning
        2 red    Critical
        3 orange Unknown
        * grey   Pending

        Nagios Output(just support 4kb data):
        shortoutput - $SERVICEOUTPUT$
        -> The first line of text output from the last service check.

        perfdata - $SERVICEPERFDATA$
        -> Contain any performance data returned by the last service check.
        With format: | 'label'=value[UOM];[warn];[crit];[min];[max].

        longoutput - $LONGSERVICEOUTPUT$
        -> The full text output aside from the first line from the last service check.

        example:
        OK - shortoutput. |
        Longoutput line1
        Longoutput line2 |
        'perfdata'=value[UOM];[warn];[crit];[min];[max]
    """

    def __init__(self):
        # Init the log.
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("monitor")
        self.logger.setLevel(logging.INFO)

        # Init output data.
        self.nagios_output = ""
        self.shortoutput = ""
        self.perfdata = []
        self.longoutput = []

        # Init the argument
        self.__define_options()
        self.define_sub_options()
        self.__parse_options()

        # Init the logger
        if self.args.debug:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug("===== BEGIN DEBUG =====")
        self.logger.debug("Init Monitor")

        # End the debug.
        if self.__class__.__name__ == "Monitor":
            self.logger.debug("===== END DEBUG =====")

    def __define_options(self):
        self.parser = argparse.ArgumentParser(description="Plugin for Monitor.")
        self.parser.add_argument('-D', '--debug',
                                 action='store_true',
                                 required=False,
                                 help='Show debug informations.',
                                 dest='debug')

    def define_sub_options(self):
        """Define options for monitoring plugins.

        Rewrite your method and define your suparsers.
        Use subparsers.add_parser to create sub options for one function.
        """
        self.plugin_parser = self.parser.add_argument_group("Plugin Options",
                                                            "Options for all plugins.")
        self.plugin_parser.add_argument("-H", "--host",
                                        default='127.0.0.1',
                                        required=True,
                                        help="Host IP address or DNS",
                                        dest="host")
        self.plugin_parser.add_argument("-u", "--user",
                                        default=None,
                                        required=False,
                                        help="User name",
                                        dest="user")
        self.plugin_parser.add_argument("-p", "--password",
                                        default=None,
                                        required=False,
                                        help="User password",
                                        dest="password")

    def __parse_options(self):
        try:
            self.args = self.parser.parse_args()
        except Exception as e:
            self.unknown("Parser arguments error: {}".format(e))

    def output(self, substitute=None, long_output_limit=None):
        """Just for nagios output and tools based on nagios except check_mk.

        Default longoutput show everything.
        But you can use long_output_limit to limit the longoutput lines.
        """
        if not substitute:
            substitute = {}

        self.nagios_output += "{0}".format(self.shortoutput)
        if self.longoutput:
            self.nagios_output = self.nagios_output.rstrip("\n")
            self.nagios_output += " | \n{0}".format(
                "\n".join(self.longoutput[:long_output_limit]))
            if long_output_limit:
                self.nagios_output += "\n(...showing only first {0} lines, " \
                    "{1} elements remaining...)".format(
                        long_output_limit,
                        len(self.longoutput[long_output_limit:]))
        if self.perfdata:
            self.nagios_output = self.nagios_output.rstrip("\n")
            self.nagios_output += " | \n{0}".format(" ".join(self.perfdata))
        return self.nagios_output.format(**substitute)

    def ok(self, msg):
        raise MonitorOk(msg)

    def warning(self, msg):
        raise MonitorWarning(msg)

    def critical(self, msg):
        raise MonitorCritical(msg)

    def unknown(self, msg):
        raise MonitorUnknown(msg)


class MonitorOk(Exception):

    def __init__(self, msg):
        print("OK - %s" % msg)
        raise SystemExit(0)


class MonitorWarning(Exception):

    def __init__(self, msg):
        print("WARNING - %s" % msg)
        raise SystemExit(1)


class MonitorCritical(Exception):

    def __init__(self, msg):
        print("CRITICAL - %s" % msg)
        raise SystemExit(2)


class MonitorUnknown(Exception):

    def __init__(self, msg):
        print("UNKNOWN - %s" % msg)
        raise SystemExit(3)


class WinRM(Monitor):

    """Basic class for WinRM."""

    def __init__(self):
        super(WinRM, self).__init__()
        self.logger.debug("Init WinRM")

        try:
            self.session = winrm.Session(self.args.host,
                                         auth=(self.args.domain + '\\' + self.args.user, self.args.password),
                                         transport=self.args.transport,
                                         service=self.args.service,
                                         server_cert_validation=self.args.scv,
                                         read_timeout_sec=self.args.rts,
                                         operation_timeout_sec=self.args.ots)
            self.logger.debug("winrm connect succeed.")
        except Exception as e:
            self.unknown("Connect by winrm error: %s" % e)

    def run_cmd(self, query):
        try:
            if query.split(",")[1:]:
                self.__result = self.session.run_cmd(str(query.split(",")[0]), query.split(",")[1:])
            else:
                self.__result = self.session.run_cmd(str(query))
            self.__return_code = self.__result.status_code
            self.__error = self.__result.std_err
            if self.__return_code:
                self.unknown("run command error: {}".format(self.__error))
            self.__output = self.__result.std_out
            return self.__output
        except Exception as e:
            self.unknown("run_cmd error: %s" % e)

    def run_ps(self, query):
        try:
            self.__result = self.session.run_ps(query)
            self.__return_code = self.__result.status_code
            self.__error = self.__result.std_err
            if self.__return_code:
                self.unknown("run powershell error: {}".format(self.__error))
            self.__output = self.__result.std_out
            return self.__output
        except Exception as e:
            self.unknown("run_ps error: %s" % e)

    def define_sub_options(self):
        super(WinRM, self).define_sub_options()
        self.wrm_parser = self.parser.add_argument_group("WinRM Options",
                                                         "options for winrm connect.")
        self.subparsers = self.parser.add_subparsers(title="WinRM Action",
                                                     description="Action mode for WinRM.",
                                                     help="Specify your action for WinRM.")
        self.wrm_parser.add_argument('-d', '--domain',
                                     required=False,
                                     help='wmi server domain.',
                                     dest='domain')
        self.wrm_parser.add_argument('--transport',
                                     default='ntlm',
                                     required=False,
                                     help='transport for winrm, default is %(default)s',
                                     dest='transport')
        self.wrm_parser.add_argument('--service',
                                     default='http',
                                     required=False,
                                     help='service for winrm, default is %(default)s',
                                     dest='service')
        self.wrm_parser.add_argument('--scv',
                                     default='ignore',
                                     required=False,
                                     help='server_cert_validation, default is %(default)s',
                                     dest='scv')
        self.wrm_parser.add_argument('--rts',
                                     default=30,
                                     type=int,
                                     help='read_timeout_sec, default is %(default)s',
                                     dest='rts')
        self.wrm_parser.add_argument('--ots',
                                     default=20,
                                     type=int,
                                     help='operation_timeout_sec, default is %(default)s',
                                     dest='ots')


class SqlserverLocks(WinRM):

    """Check the attribute related to MSSQLSERVER_SQLServerLocks wmi class use WinRM."""

    def __init__(self):
        super(SqlserverLocks, self).__init__()
        self.logger.debug("Init SqlserverLocks")

    def define_sub_options(self):
        super(SqlserverLocks, self).define_sub_options()
        self.sl_parser = self.subparsers.add_parser('sqlserverlocks',
                                                    help='Options for SqlserverLocks',
                                                    description='All options for SqlserverLocks')
        self.sl_parser.add_argument('-q', '--query',
                                    required=False,
                                    help='cmd and powershell for winrm, like "ipconfig, /all"',
                                    dest='query')
        self.sl_parser.add_argument('-m', '--mode',
                                    required=True,
                                    help='From ["LockTimeoutsPersec", "LockWaitsPersec", "NumberofDeadlocksPersec"]',
                                    dest='mode')
        self.sl_parser.add_argument('-w', '--warning',
                                    default=0,
                                    type=int,
                                    required=False,
                                    help='Default is %(default)s',
                                    dest='warning')
        self.sl_parser.add_argument('-c', '--critical',
                                    default=0,
                                    type=int,
                                    required=False,
                                    help='Default is %(default)s',
                                    dest='critical')

    def sqlserverlocks_handle(self):
        self.ok_list = []
        self.warn_list = []
        self.crit_list = []
        status = self.ok

        self.__results = self.run_ps("""Get-WmiObject -Query "select * from Win32_PerfFormattedData_MSSQLSERVER_SQLServerLocks" | Format-List -Property Name,%s """ % self.args.mode)
        self.logger.debug("results: {}".format(self.__results))
        self.__results_list = self.__results.split()
        self.logger.debug("results list: {}".format(self.__results_list))
        # ['Name', ':', 'OibTrackTbl', 'LockTimeoutsPersec', ':', '0']
        self.__results_format_list = []
        [self.__results_format_list.append(value) for value in self.__results_list if value != ":" and value != "Name" and value != self.args.mode]
        self.logger.debug("results format list: {}".format(self.__results_format_list))
        # ['OibTrackTbl', '0', 'AllocUnit', '0', 'HoBT', '0', 'Metadata', '0']
        self.__results_format_dict = []
        for loop in range(0, len(self.__results_format_list)):
            if loop % 2 == 0:
                Name = self.__results_format_list[loop]
            else:
                Value = self.__results_format_list[loop]
                one_dict = {"Name": Name, self.args.mode: Value}
                self.__results_format_dict.append(one_dict)
        self.logger.debug("results format dict: {}".format(self.__results_format_dict))
        # [{'LockTimeoutsPersec': '0', 'Name': 'File'}, {'LockTimeoutsPersec': '0', 'Name': 'Database'}]

        for lock_dict in self.__results_format_dict:
            self.name = lock_dict.get('Name')
            self.logger.debug("name: {}".format(self.name))
            self.value = int(lock_dict.get(self.args.mode))
            self.logger.debug("value: {}".format(self.value))
            if self.value > self.args.critical:
                self.crit_list.append(self.name + " : " + self.value)
            elif self.value > self.args.warning:
                self.warn_list.append(self.name + " : " + self.value)
            else:
                self.ok_list.append(self.name + " : " + str(self.value))

        if self.crit_list:
            status = self.critical
        elif self.warn_list:
            status = self.warning
        else:
            status = self.ok

        self.shortoutput = "Found {0} {1} critical.".format(len(self.crit_list), self.args.mode)
        if self.crit_list:
            self.longoutput.append("===== Critical ====")
        [self.longoutput.append(filename) for filename in self.crit_list if self.crit_list]
        if self.warn_list:
            self.longoutput.append("===== Warning ====")
        [self.longoutput.append(filename) for filename in self.warn_list if self.warn_list]
        if self.ok_list:
            self.longoutput.append("===== OK ====")
        [self.longoutput.append(filename) for filename in self.ok_list if self.ok_list]
        self.perfdata.append("{mode}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=len(self.crit_list),
            mode=self.args.mode))

        # Return status and output to monitoring server.
        self.logger.debug("Return status and output.")
        status(self.output())


class MostRecentFileAge(WinRM):

    """Check the Most Recent File Age."""

    def __init__(self):
        super(MostRecentFileAge, self).__init__()
        self.logger.debug("Init MostRecentFileAge")

    def define_sub_options(self):
        super(MostRecentFileAge, self).define_sub_options()
        self.mr_parser = self.subparsers.add_parser('mostrecentfileage',
                                                    help='Get age of most recent file.',
                                                    description='Options\
                                                    for most recent file age.')
        self.mr_parser.add_argument('-q', '--query',
                                    required=False,
                                    help='wql or cmd.',
                                    dest='wql or cmd')
        self.mr_parser.add_argument('-d', '--drive',
                                    required=False,
                                    help='the windows driver, like C:',
                                    dest='drive')
        self.mr_parser.add_argument('-p', '--path',
                                    default="\\\\",
                                    required=False,
                                    help='the folder, default is %(default)s',
                                    dest='path')
        self.mr_parser.add_argument('-f', '--filename',
                                    default="*",
                                    required=False,
                                    help='the filename, default is %(default)s',
                                    dest='filename')
        self.mr_parser.add_argument('-e', '--extension',
                                    default="txt",
                                    required=False,
                                    help='the file extension, default is %(default)s',
                                    dest='extension')
        self.mr_parser.add_argument('-R', '--recursion',
                                    action='store_true',
                                    help='Recursive count file under path.',
                                    dest='recursion')
        self.mr_parser.add_argument('-w', '--warning',
                                    default=30,
                                    type=int,
                                    required=False,
                                    help='Warning minute of file, default is %(default)s',
                                    dest='warning')
        self.mr_parser.add_argument('-c', '--critical',
                                    default=60,
                                    type=int,
                                    required=False,
                                    help='Critical minute of file, default is %(default)s',
                                    dest='critical')

    def mostrecentfileage_handle(self):
        status = self.ok

        self.file_list = self.run_ps("""Get-ChildItem D:\\test\\* -include *.txt
                                     | Format-List -Property Name,LastWriteTime""")
        self.logger.debug("file: {}".format(self.file_list))

        # Return status and output to monitoring server.
        self.logger.debug("Return status and output.")
        status(self.output())


class Register(SqlserverLocks, MostRecentFileAge):

    """Register your own class here."""

    def __init__(self, *args, **kwargs):
        super(Register, self).__init__()


def main():
    """Register your own mode and handle method here."""
    plugin = Register()
    arguments = sys.argv[1:]
    if 'sqlserverlocks' in arguments:
        plugin.sqlserverlocks_handle()
    elif 'mostrecentfileage' in arguments:
        plugin.mostrecentfileage_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
