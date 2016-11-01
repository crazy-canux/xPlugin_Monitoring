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


import os
import sys
# import re
import logging
import argparse
# import pickle
import ftplib


class Nagios(object):

    """Basic class for nagios."""

    def __init__(self, name=None, version='1.0.0', description='For Ftp'):
        """Init class Nagios."""
        self._name = os.path.basename(sys.argv[0]) if not name else name
        self.__version = version
        self.__description = description

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("ftp")
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
        self.parser = argparse.ArgumentParser(description="Plugin for ftp.")
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
        self.ftp_parser = self.parser.add_argument_group('ftp options',
                                                         'For ftp connect.')
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


class Ftp(Nagios):
    """Basic class for ftp."""
    def __init__(self, *args, **kwargs):
        super(Ftp, self).__init__(*args, **kwargs)
        self.logger.debug("Init Ftp")

    def connect(self):
        """Connect to ftp server."""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(host=self.args.host,
                             port=self.args.port,
                             timeout=self.args.timeout)
            self.ftp.login(user=self.args.user,
                           passwd=self.args.password,
                           acct=self.args.acct)
            return self.ftp
        except ftplib.Error as e:
            self.unknown("Can not connect to the ftp: %s" % e)

    def quit(self):
        """Close and exit the connection."""
        try:
            self.ftp.quit()
            self.logger.debug("quit connect ok")
        except ftplib.Error as e:
            self.unknown("quit connect error: %s" % e)

    def define_sub_options(self):
        super(Ftp, self).define_sub_options()
        self.ftp_parser.add_argument('-H', '--host',
                                     required=True,
                                     help='ftp server host.',
                                     dest='host')
        self.ftp_parser.add_argument('-p', '--port',
                                     default='21',
                                     type=int,
                                     required=False,
                                     help='ftp server port.',
                                     dest='port')
        self.ftp_parser.add_argument('-t', '--timeout',
                                     default=-999,
                                     type=int,
                                     required=False,
                                     help='ftp timeout, default -999',
                                     dest='timeout')
        self.ftp_parser.add_argument('-u', '--user',
                                     required=True,
                                     help='ftp login username.',
                                     dest='user')
        self.ftp_parser.add_argument('-P', '--password',
                                     required=True,
                                     help='ftp login password.',
                                     dest='password')
        self.ftp_parser.add_argument('-a', '--acct',
                                     default='',
                                     required=False,
                                     help='acct for ftp login, default null',
                                     dest='acct')


class FileNumber(Ftp):
    """Count the file number in the ftp folder."""
    def __init__(self, *args, **kwargs):
        super(FileNumber, self).__init__(*args, **kwargs)
        self.logger.debug("Init FileNumber")

    def define_sub_options(self):
        super(FileNumber, self).define_sub_options()
        self.fn_parser = self.subparsers.add_parser('filenumber',
                                                    help='Count file number.',
                                                    description='Options\
                                                    for filenumber.')
        self.fn_parser.add_argument('-p', '--path',
                                    required=True,
                                    help='The folder you want to count.',
                                    dest='path')
        self.fn_parser.add_argument('-r', '--regex',
                                    required=False,
                                    help='RE for filename or extension',
                                    dest='regex')
        self.fn_parser.add_argument('-R', '--recursive',
                                    required=False,
                                    help='Recursive count file under path.',
                                    dest='recursive')
        self.fn_parser.add_argument('-w', '--warning',
                                    default=0,
                                    type=int,
                                    required=False,
                                    help='Warning value for filenumber',
                                    dest='warning')
        self.fn_parser.add_argument('-c', '--critical',
                                    default=0,
                                    type=int,
                                    required=False,
                                    help='Critical value for filenumber',
                                    dest='critical')

    def filenumber_handle(self):
        """Get the number of files in the folder"""
        self.__results = []
        self.__dirs = []
        self.__files = []
        self.__ftp = self.connect()
        self.__ftp.dir(self.args.path, self.__results.append)
        # self.logger.debug("dir results: {}".format(self.__results))
        self.quit()

        status = self.ok

        for data in self.__results:
            if "<DIR>" in data:
                self.__dirs.append(str(data.split()[3]))
            else:
                self.__files.append(str(data.split()[2]))

        self.__result = len(self.__files)
        self.logger.debug("result: {}".format(self.__result))

        # Compare the vlaue.
        if self.__result > self.args.warning:
            status = self.warning
        if self.__result > self.args.critical:
            status = self.critical

        # Output
        self.shortoutput = "Found {0} files in {1}.".format(self.__result,
                                                            self.args.path)
        [self.longoutput.append(line) for line in self.__results if self.__results]
        self.perfdata.append("{path}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=self.__result,
            path=self.args.path))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class Diff(FileNumber):
    def __init__(self, *args, **kwargs):
        super(Diff, self).__init__(*args, **kwargs)


def main():
    plugin = Diff()
    arguments = sys.argv[1:]
    if 'filenumber' in arguments:
        plugin.filenumber_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
