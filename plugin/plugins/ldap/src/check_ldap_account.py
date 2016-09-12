#!/usr/bin/env python

################################################################################
#
# check_ldap_account.py: check LDAP Account
#
#
# Usage: check_ldap_account.py [-h] [--debug] [--version] 
#                              -H host_ad
#                              -s account_search
#                              [-b base_dn]
#                              [-l login] [-p password]
#
# Create: 14/01/2013
# Author: BAILAT Patrick
#
# Modify: JJ/MM/AAAA
# Author:
# Object:
#
################################################################################

import logging
import traceback
import ldap
import time
from pprint import pformat
from monitoring.nagios.plugin import NagiosPlugin

logger = logging.getLogger('plugin.ldap')

# define new args 
class PluginLdap(NagiosPlugin):
    def define_plugin_arguments(self):
        super(PluginLdap,self).define_plugin_arguments()

        self.required_args.add_argument('-s', '--accountsearch',
                                        dest="account_search",
                                        help="Acount Search, an string",
                                        required=True)

        self.required_args.add_argument('-l', '--login',
                                        dest="login_dn",
                                        help="Login dn, an string",
                                        default='CN=9NagiosDC,OU=Daemons,OU=EU-Nagios,OU=Applications,DC=corp',
                                        )

        self.required_args.add_argument('-p', '--passwd',
                                        dest="passwd",
                                        help="Password, an string",
                                        default='NglP(23M,n',
                                        )

        self.required_args.add_argument('-b', '--basedn',
                                        dest="base_dn",
                                        help="Bese dn, an string",
                                        default='corp',
                                        )
# Init plugin
plugin = PluginLdap(version="1.0",
                    description="check Account LDAP" )
plugin.shortoutput = "Account LDAP {0} exists".format(plugin.options.account_search)


# Final status exit for the plugin
status = None

# LDAP
try:
    l = ldap.initialize('ldap://{0}:3268'.format(plugin.options.hostname))
    l.simple_bind(plugin.options.login_dn, plugin.options.passwd)
except:
    plugin.unknown('LDAP connection error !\n{}'.format(traceback.format_exc()))

# Search
try:
    result = l.search_st('DC={0}'.format(plugin.options.base_dn), ldap.SCOPE_SUBTREE, '(&(objectClass=user)(objectcategory=person)(cn={0}))'.format(plugin.options.account_search), ['CN', 'UserAccountControl'], 0, 30)
except:
    try:
        time.sleep( 5 )
        result = l.search_st('DC={0}'.format(plugin.options.base_dn), ldap.SCOPE_SUBTREE, '(&(objectClass=user)(objectcategory=person)(cn={0}))'.format(plugin.options.account_search), ['CN', 'UserAccountControl'], 0, 30)
    except:
        plugin.unknown('LDAP search error !\n{}'.format(traceback.format_exc()))


logger.debug("result:\n{0}".format(pformat(result)))

if not result:
    status=plugin.critical
    plugin.shortoutput = "Account LDAP {0} no exists".format(plugin.options.account_search)
else:
    status = plugin.ok
    msg = ""
    msg_err = ""
    for entry in result:
        dn, attributes = entry
        logger.debug(pformat(entry))
        logger.debug(attributes)

        if attributes.has_key('userAccountControl'):
            account_ctrl = attributes['userAccountControl'].pop()
            cn = attributes['cn'].pop()
            logger.debug(account_ctrl)

            if account_ctrl == '512':
                logger.info('NORMAL_ACCOUNT')
                plugin.shortoutput = "Problem UserAccountControl {0}".format(plugin.options.account_search)
                status = plugin.warning
                msg_err += "{0} : NORMAL_ACCOUNT\n".format(cn)
            elif account_ctrl == '66048':
                logger.info('DONT_EXPIRE_PASSWORD')
                msg += "{0} : DONT_EXPIRE_PASSWORD\n".format(cn)
            elif account_ctrl == '514':
                logger.info('ACCOUNTDISABLE')
                plugin.shortoutput = "Problem UserAccountControl {0}".format(plugin.options.account_search)
                status = plugin.critical
                msg_err += "{0} : ACCOUNTDISABLE\n".format(cn)
            elif account_ctrl == '528':
                logger.info('VERROUILLAGE')
                plugin.shortoutput = "Problem UserAccountControl {0}".format(plugin.options.account_search)
                status = plugin.critical
                msg_err += "{0} : VERROUILLAGE\n".format(cn)
            elif account_ctrl == '8388608' or account_ctrl == '8389120':
                logger.info('PASSWORD_EXPIRED')
                plugin.shortoutput = "Problem UserAccountControl {0}".format(plugin.options.account_search)
                status = plugin.critical
                msg_err += "{0} : PASSWORD_EXPIRED\n".format(cn)
            else:
                plugin.shortoutput = "Problem UserAccountControl {0}".format(plugin.options.account_search)
                status = plugin.critical
                msg_err += "{0} : UserAccountControl ({1})\n".format(cn, account_ctrl)
        else:
            status = plugin.warning
            msg_err += "no UserAccountControl for {0} \n".format(dn)

    plugin.longoutput.append("  -   Erreur :\n{0} \n  -  Normal : \n{1}".format(msg_err, msg))

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
   status(plugin.output())
else:
   plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
