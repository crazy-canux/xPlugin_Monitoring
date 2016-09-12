# -*- coding: utf-8 -*-
# Copyright (c) EIT/PLM Delivery <dl-it-systemoperating-eitapplications>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""NetApp storage module."""

import re
import logging

from .base import StoragePluginSNMP

logger = logging.getLogger('plugin.storage')


class PluginCheckNetappVolume(StoragePluginSNMP):
    """Plugin that check NetApp Volume storage."""
    def define_plugin_arguments(self):
        """Define new specific arguments."""
        super(PluginCheckNetappVolume, self).define_plugin_arguments()

        self.required_args.add_argument('-w',
                                        dest='warning',
                                        default='0',
                                        type=int,
                                        help='Warn if volume size are above '
                                             'this threshold in %%.')
        self.required_args.add_argument('-c',
                                        dest='critical',
                                        default='0',
                                        type=int,
                                        help='Crit if volume size  are above '
                                             'this threshold in %%.')
        self.required_args.add_argument('-r',
                                        dest='regexp',
                                        default='.*',
                                        type=re.compile,
                                        help='Regexp pattern to filter '
                                             'volumes. Default to all \'.*\'.')
        self.required_args.add_argument('-e',
                                        dest='exc_regexp',
                                        type=re.compile,
                                        help='Regexp pattern to exclude '
                                             'volumes.')

    def verify_plugin_arguments(self):
        """Sanity check for plugin arguments."""
        super(PluginCheckNetappVolume, self).verify_plugin_arguments()

        # Thresholds
        if self.options.warning and self.options.critical:
            if self.options.warning > self.options.critical:
                self.unknown('Warning threshold cannot be above critical !')
            elif self.options.warning < 0 or self.options.critical < 0:
                self.unknown('Warning / Critical threshold cannot be below '
                             'zero !')

    def main(self):
        """Main plugin entry point."""
        # vol_size : dfPerCentKBytesCapacity
        # vol_name : dfMountedOn
        oids = {
            'vol_name': '1.3.6.1.4.1.789.1.5.4.1.10',
            'vol_size': '1.3.6.1.4.1.789.1.5.4.1.6',
        }

        snmpquery = self.snmp.getnext(oids)

        self.shortoutput = "all volume ({0}) size are below " \
                           "the thresholds".format(self.options.regexp.pattern)

        msg_err_warn = "# ======= {0} WARNING ========"
        msg_err_crit = "# ======= {0} CRITICAL ========"

        cmpt_warn = 0
        cmpt_crit = 0

        msg = ""

        status = self.ok
        for result in snmpquery['vol_name']:
            name = str(result.value)
            if self.options.exc_regexp:
                if self.options.exc_regexp.search(name):
                    continue
            if self.options.regexp.search(name):
                vol_size = [e.pretty()
                            for e in snmpquery['vol_size']
                            if e.index == result.index][0]
                vol_size = int(vol_size)
                # Performance data
                self.perfdata.append(
                    '"{1}"={2}%;{0.warning};{0.critical};0;100;'.format(
                        self.options, name, vol_size))
                logger.debug("oid {0.oid}, "
                             "vol_name {0.value}, "
                             "index: {0.index}, "
                             "size: {1}".format(result, vol_size))
                # Check threshold
                if self.options.critical:
                    if vol_size >= self.options.critical:
                        status = self.critical
                        msg_err_crit += "\n Volume {0} : {1} ".format(name,
                                                                      vol_size)
                        cmpt_crit += 1
                        continue
                if self.options.warning:
                    if vol_size >= self.options.warning:
                        cmpt_warn += 1
                        msg_err_warn += "\n Volume {0} : {1} ".format(name,
                                                                      vol_size)
                        if status != self.critical:
                            status = self.warning

        if cmpt_crit > 0:
            self.longoutput.append(msg_err_crit.format(cmpt_crit))
            msg += "{0} Volume size > critical threshold ({1}%)".format(
                cmpt_crit, self.options.critical)
        if cmpt_warn > 0:
            self.longoutput.append(msg_err_warn.format(cmpt_warn))
            if msg:
                msg += " and "
            msg += "{0} Volume size > warning threshold ({1}%)".format(
                cmpt_warn, self.options.warning)
        if msg:
            self.shortoutput = msg
            logger.debug(msg)

        # Returns output and status to Nagios
        status(self.output())


class PluginCheckNetappSnapshot(StoragePluginSNMP):
    """Plugin that check available NetApp snapshots."""
    def define_plugin_arguments(self):
        """Define new specific arguments."""
        super(PluginCheckNetappSnapshot, self).define_plugin_arguments()

        self.required_args.add_argument('-w',
                                        dest='warning',
                                        default='0',
                                        type=int,
                                        help='Warning if available snapshot is '
                                             'above this threshold.')
        self.required_args.add_argument('-c',
                                        dest='critical',
                                        default='0',
                                        type=int,
                                        help='Critical if available snapshot '
                                             'is above this threshold.')
        self.required_args.add_argument('-r',
                                        dest='regexp',
                                        default='.*',
                                        type=re.compile,
                                        help='Regexp pattern to filter '
                                             'volumes. Default to all \'.*\'.')
        self.required_args.add_argument('-e',
                                        dest='exc_regexp',
                                        type=re.compile,
                                        help='Regexp pattern to exclude '
                                             'volumes.')

    def verify_plugin_arguments(self):
        """Sanity check for plugin arguments."""
        super(PluginCheckNetappSnapshot, self).verify_plugin_arguments()

        # Thresholds
        if self.options.warning and self.options.critical:
            if self.options.warning > self.options.critical:
                self.unknown('Warning threshold cannot be above critical !')
            elif self.options.warning < 0 or self.options.critical < 0:
                self.unknown('Warning / Critical threshold cannot be below '
                             'zero !')

    def main(self):
        """Main plugin entry point."""
        # vol_name : dfMountedOn
        oids = {
            'vol_name': '1.3.6.1.4.1.789.1.5.4.1.10'
        }

        snmpquery = self.snmp.getnext(oids)

        snap_num = 0
        msg_ok = "{0} available snapshot matching '{1}'{threshold}"
        msg_alert = "{0} available snapshot matching '{1}' (>= {2})"

        status = self.ok
        for result in snmpquery['vol_name']:
            name = str(result.value)
            if self.options.exc_regexp:
                if self.options.exc_regexp.search(name):
                    continue
            if self.options.regexp.search(name):
                snap_num += 1
                self.longoutput.append("Snapshot: {0.value}".format(result))
                logger.debug("oid: {0.oid}, "
                             "snap_name: {0.value}, "
                             "index: {0.index}".format(result))

        # Check against thresholds
        if self.options.critical or self.options.warning:
            state = msg_ok.format(snap_num,
                                  self.options.regexp.pattern,
                                  threshold=" (< %s)" % self.options.warning)

            if snap_num >= self.options.critical:
                status = self.critical
                state = msg_alert.format(snap_num,
                                         self.options.regexp.pattern,
                                         self.options.critical)
            elif snap_num >= self.options.warning:
                status = self.warning
                state = msg_alert.format(snap_num,
                                         self.options.regexp.pattern,
                                         self.options.warning)
        else:
            state = msg_ok.format(snap_num,
                                  self.options.regexp.pattern,
                                  threshold="")

        # Performance data
        self.perfdata.append(
            '"snapshot_number"={1}s;{0.warning};{0.critical};0;'.format(
                self.options, snap_num))

        self.shortoutput = state

        # Returns output and status to Nagios
        status(self.output())
