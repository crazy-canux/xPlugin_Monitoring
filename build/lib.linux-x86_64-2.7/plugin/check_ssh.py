#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Copyright (C) 2015 Faurecia (China) Holding Co.,Ltd.

All rights reserved.
Name: check_ssh.py
Author: Canux CHENG canuxcheng@gmail.com
Version: V1.0.0.0
Time: Thu 28 Jul 2016 04:44:53 PM CST

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
import string
import socket

import paramiko


class Nagios(object):

    """Basic class for nagios."""

    def __init__(self, name=None, version='1.0.0.0', description='For ssh'):
        """Init class Nagios."""
        self.__name = os.path.basename(sys.argv[0]) if not name else name
        self.__version = version
        self.__description = description

        # Init the log
        logging.basicConfig(format='[%(levelname)s] (%(module)s) %(message)s')
        self.logger = logging.getLogger("ssh")
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
        self.parser = argparse.ArgumentParser(description="Plugin for ssh.")
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
        self.ssh_parser = self.parser.add_argument_group('ssh options',
                                                         'For ssh connect.')
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


class Ssh(Nagios):

    """Basic class for ssh."""

    def __init__(self, *args, **kwargs):
        super(Ssh, self).__init__(*args, **kwargs)
        self.logger.debug("Init ssh")
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=self.args.host,
                             port=self.args.port,
                             username=self.args.user,
                             password=self.args.password,
                             pkey=None,
                             key_filename=None,
                             timeout=self.args.timeout,
                             allow_agent=True,
                             look_for_keys=True,
                             compress=False,
                             sock=None)
        except paramiko.SSHException as e:
            self.unknown("Can not connect to server with SSH: %s" % e)

    def execute(self, command, timeout=None):
        """Execute a shell command."""
        try:
            self.channel = self.ssh.get_transport().open_session()
        except paramiko.SSHException as e:
            self.unknown("Create channel error: %s" % e)
        try:
            self.channel.settimeout(self.args.timeout if not timeout else timeout)
        except socket.timeout as e:
            self.unknown("Settimeout for channel error: %s" % e)
        try:
            self.logger.debug("command: {}".format(command))
            self.channel.exec_command(command)
        except paramiko.SSHException as e:
            self.unknown("Execute command error: %s" % e)
        try:
            self.stdin = self.channel.makefile('wb', -1)
            self.stderr = map(string.strip, self.channel.makefile_stderr('rb', -1).readlines())
            self.stdout = map(string.strip, self.channel.makefile('rb', -1).readlines())
        except Exception as e:
            self.unknown("Get result error: %s" % e)
        try:
            self.status = self.channel.recv_exit_status()
        except paramiko.SSHException as e:
            self.unknown("Get return code error: %s" % e)
        else:
            if self.status != 0:
                self.unknown("Return code: %d , stderr: %s" % (self.status, self.errors))
            else:
                return self.stdout
        finally:
            self.logger.debug("Execute command finish.")

    def close(self):
        """Close and exit the connection."""
        try:
            self.ssh.close()
            self.logger.debug("close connect ok")
        except paramiko.SSHException as e:
            self.unknown("close connect error: %s" % e)

    def define_sub_options(self):
        super(Ssh, self).define_sub_options()
        self.ssh_parser.add_argument('-H', '--host',
                                     required=True,
                                     help='ssh server host.',
                                     dest='host')
        self.ssh_parser.add_argument('-p', '--port',
                                     default='22',
                                     type=int,
                                     required=False,
                                     help='ssh server port, default is %(default)s.',
                                     dest='port')
        self.ssh_parser.add_argument('-t', '--timeout',
                                     default=60,
                                     type=int,
                                     required=False,
                                     help='ssh timeout, default is %(default)s',
                                     dest='timeout')
        self.ssh_parser.add_argument('-u', '--user',
                                     required=False,
                                     help='ssh login username.',
                                     dest='user')
        self.ssh_parser.add_argument('-P', '--password',
                                     required=False,
                                     help='ssh login password.',
                                     dest='password')


class Command(Ssh):

    """Run a command by SSH and return a single number."""

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.logger.debug("Init Command")

    def define_sub_options(self):
        super(Command, self).define_sub_options()
        self.cm_parser = self.subparsers.add_parser('command',
                                                    help='Run shell command.',
                                                    description='Options\
                                                    for command.')
        self.cm_parser.add_argument('-C', '--command',
                                    required=True,
                                    help='The shell command.',
                                    dest='command')
        self.cm_parser.add_argument('-w', '--warning',
                                    default=0,
                                    type=int,
                                    required=False,
                                    help='Warning value for Command, default is %(default)s',
                                    dest='warning')
        self.cm_parser.add_argument('-c', '--critical',
                                    default=0,
                                    type=int,
                                    required=False,
                                    help='Critical value for Command, default is %(default)s',
                                    dest='critical')

    def command_handle(self):
        """Get the number of the shell command."""
        self.__results = self.execute(self.args.command)
        self.close()

        self.logger.debug("results: {}".format(self.__results))
        if not self.__results:
            self.unknown("{} return nothing.".format(self.args.command))
        if len(self.__results) != 1:
            self.unknown("{} return more than one number.".format(self.args.command))
        self.__result = int(self.__results[0])
        self.logger.debug("result: {}".format(self.__result))
        if not isinstance(self.__result, (int, long)):
            self.unknown("{} didn't return single number.".format(self.args.command))

        status = self.ok
        # Compare the vlaue.
        if self.__result > self.args.warning:
            status = self.warning
        if self.__result > self.args.critical:
            status = self.critical

        # Output
        self.shortoutput = "{0} return {1}.".format(self.args.command, self.__result)
        [self.longoutput.append(line) for line in self.__results if self.__results]
        self.perfdata.append("{command}={result};{warn};{crit};0;".format(
            crit=self.args.critical,
            warn=self.args.warning,
            result=self.__result,
            command=self.args.command))

        # Return status with message to Nagios.
        status(self.output(long_output_limit=None))
        self.logger.debug("Return status and exit to Nagios.")


class Register(Command):

    """Register your own class here."""

    def __init__(self, *args, **kwargs):
        super(Register, self).__init__(*args, **kwargs)


def main():
    """Register your own mode and handle method here."""
    plugin = Register()
    arguments = sys.argv[1:]
    if 'command' in arguments:
        plugin.command_handle()
    else:
        plugin.unknown("Unknown actions.")

if __name__ == "__main__":
    main()
