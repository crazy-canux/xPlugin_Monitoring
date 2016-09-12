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

import logging
from pprint import pformat
from monitoring.nagios.plugin import NagiosPluginWMI


logger = logging.getLogger('plugin.wmi')

# define new args
class PluginWMI(NagiosPluginWMI):
    def define_plugin_arguments(self):
        super(PluginWMI,self).define_plugin_arguments()

        self.required_args.add_argument('-s', '--accountsearch',
                                        dest="account_search",
                                        help="Acount Search, an string",
                                        required=True)

# Init plugin
plugin = PluginWMI(version="1.2.0", description="check Local Account Windows" )
plugin.shortoutput = "Local Account {0} exists".format(plugin.options.account_search)



# Final status exit for the plugin
status = None



# Declaration CMD
cmd="SELECT Name,Disabled,Lockout,PasswordChangeable,PasswordExpires,PasswordRequired,Status FROM Win32_UserAccount WHERE Name='{0}'".format(plugin.options.account_search)
result = plugin.execute(cmd)

logger.debug(result)

if not result:
    status = plugin.critical
    plugin.shortoutput = "Local Account {0} no exists".format(plugin.options.account_search)
else:
    status = plugin.ok
    msg_err = ""
    for entry in result:
        logger.debug(pformat(entry))

        if entry.has_key('Disabled'):
            account_disabled = entry['Disabled']
            logger.debug(account_disabled)

            if account_disabled == 'True':
                status = plugin.critical
                plugin.shortoutput = "Local Account {0} is disabled !".format(plugin.options.account_search)
                msg_err += "{0} : DISABLED\n".format(plugin.options.account_search)
        if entry.has_key('Lockout'):
            account_lockout = entry['Lockout']
            logger.debug(account_lockout)

            if account_lockout == 'True':
                status = plugin.critical
                plugin.shortoutput = "Local Account {0} is locked out !".format(plugin.options.account_search)
                msg_err += "{0} : LOCKED OUT\n".format(plugin.options.account_search)
        if entry.has_key('PasswordChangeable'):
            account_PasswordChangeable = entry['PasswordChangeable']
            logger.debug(account_PasswordChangeable)

            if account_PasswordChangeable == 'False':
                status = plugin.critical
                plugin.shortoutput = "Password for Local Account {0} can not be changed !".format(plugin.options.account_search)
                msg_err += "{0} : PASSWORD CAN NOT BE CHANGED\n".format(plugin.options.account_search)
        if entry.has_key('PasswordExpires'):
            account_PasswordExpires = entry['PasswordExpires']
            logger.debug(account_PasswordExpires)

            if account_PasswordExpires == 'True':
                status = plugin.critical
                plugin.shortoutput = "Password for Local Account {0} expires !".format(plugin.options.account_search)
                msg_err += "{0} : PASSWORD EXPIRES\n".format(plugin.options.account_search)
        if entry.has_key('PasswordRequired'):
            account_PasswordRequired = entry['PasswordRequired']
            logger.debug(account_PasswordRequired)

            if account_PasswordRequired == 'False':
                status = plugin.critical
                plugin.shortoutput = "Password for Local Account {0} does not required !".format(plugin.options.account_search)
                msg_err += "{0} : PASSWORD DOES NOT REQUIRED\n".format(plugin.options.account_search)

        if entry.has_key('Status'):
            account_Status = entry['Status']
            logger.debug(account_Status)

            if account_Status != "OK":
                if account_Status == "Degraded" or account_Status == "Pred Fail":
                    if status == plugin.ok:
                        status = plugin.warning
                        plugin.shortoutput = "Local Account {0} is operational, Status : {1}, predicts a failure in the near future".format(plugin.options.account_search,account_Status)
                        msg_err += "{0} - STATUS : {1}\n".format(plugin.options.account_search,account_Status)
                else:
                    status = plugin.critical
                    plugin.shortoutput = "Local Account {0} is not operational, Status : {1}".format(plugin.options.account_search,account_Status)
                    msg_err += "{0} - STATUS : {1}\n".format(plugin.options.account_search,account_Status)

    if msg_err != "":
        plugin.longoutput.append(" - Error :\n{0}".format(msg_err))




# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
   status(plugin.output())
else:
   plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
