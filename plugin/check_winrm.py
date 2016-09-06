#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Copyright (C) 2015 Faurecia (China) Holding Co.,Ltd.

All rights reserved.
Name: check_winrm.py
Author: Canux CHENG canuxcheng@gmail.com
Version: V1.0.0.0
Time: Thur 01 Aug 2016 04:43:40 PM CST

WinRM: Windows Remote Management.
Windows Remote Management (WinRM) is the Microsoft implementation of WS-Management Protocol,
a standard Simple Object Access Protocol (SOAP)-based,
firewall-friendly protocol that allows hardware and operating systems,
from different vendors, to interoperate.

Description:
    [1.0.0.0] 20160728 init for basic function.
"""
import os
import sys
import logging
import argparse
# try:
#     import cPickle as pickle
# except:
#     import pickle

import winrm


class Nagios(object):

    """Basic class for nagios."""

    def __init__(self, name=None, version='1.0.0.0', description='For wrm'):
        """Init class Nagios."""
        self.__name = os.path.basename(sys.argv[0]) if not name else name
        self.__version = version
        self.__description = description

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("wrm")
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
        self.parser = argparse.ArgumentParser(description="Plugin for wrm.")
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
        self.wrm_parser = self.parser.add_argument_group('wrm options',
                                                         'For wrm connect.')
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
            self.output_ += " | \n{0}".format(
                "\n".join(self.longoutput[:long_output_limit]))
            if long_output_limit:
                self.output_ += "\n(...showing only first {0} lines, " \
                    "{1} elements remaining...)".format(
                        long_output_limit,
                        len(self.longoutput[long_output_limit:]))
        if self.perfdata:
            self.output_ = self.output_.rstrip("\n")
            self.output_ += " | \n{0}".format(" ".join(self.perfdata))
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


class WinRM(Nagios):

    """Basic class for WinRM."""

    def __init__(self, *args, **kwargs):
        super(WinRM, self).__init__(*args, **kwargs)
        self.logger.debug("Init winrm")
        try:
            self.session = winrm.Session(self.args.host,
                                         auth=(self.args.domain + '\\' + self.args.user, self.args.password),
                                         transport=self.args.transport,
                                         service=self.args.service,
                                         server_cert_validation=self.args.scv,
                                         read_timeout_sec=self.args.rts,
                                         operation_timeout_sec=self.args.ots)
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
        self.wrm_parser.add_argument('-H', '--host',
                                     required=True,
                                     help='wmi server host.',
                                     dest='host')
        self.wrm_parser.add_argument('-d', '--domain',
                                     required=False,
                                     help='wmi server domain.',
                                     dest='domain')
        self.wrm_parser.add_argument('-u', '--user',
                                     required=True,
                                     help='wmi username',
                                     dest='user')
        self.wrm_parser.add_argument('-p', '--password',
                                     required=True,
                                     help='wmi login password.',
                                     dest='password')
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

    """Check the attribute related to MSSQLSERVER_SQLServerLocks wmi class use WinRM.

    Example:
        check_winrm.py -H HOSTNAME -d [Domain] -u USER -p [password] --debug sqlserverlocks -m LockTimeoutsPersec -w 0 -c 0
        check_winrm.py -H HOSTNAME -d [Domain] -u USER -p [password] --debug sqlserverlocks -m LockWaitsPersec -w 0 -c 0
    """

    def __init__(self, *args, **kwargs):
        super(SqlserverLocks, self).__init__(*args, **kwargs)
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

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class Register(SqlserverLocks):

    """Register your own class here."""

    def __init__(self, *args, **kwargs):
        super(Register, self).__init__(*args, **kwargs)


def main():
    """Register your own mode and handle method here."""
    plugin = Register()
    arguments = sys.argv[1:]
    if 'sqlserverlocks' in arguments:
        plugin.sqlserverlocks_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
