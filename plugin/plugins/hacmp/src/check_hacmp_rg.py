#!/usr/bin/env python

################################################################################
#
# check_hacmp_rg.py: check statut of RG
#
# Usage: check_hacmp.py [-h] [--debug] [--version] -H HOSTNAME
#                       [-g RG1 RG2 ...RGn] [-a RG]
#
# Create: 23/11/2012
# Author: BAILAT Patrick
#
# Modify: 03/04/2013
# Author: BAILAT Patrick
# Object: check if SNMP query is empty
#
################################################################################

import re
import logging
import traceback
from monitoring.nagios.plugin import NagiosPluginSNMP
from collections import Counter
import hacmp

logger = logging.getLogger('plugin.hacmp')

# define new args
class PluginHacmpRg(NagiosPluginSNMP):
    def define_plugin_arguments(self):
        super(PluginHacmpRg,self).define_plugin_arguments()

        self.required_args.add_argument('-a', '--alone',
                                        dest="rg_alone",
                                        help="Check RG is alone, an string",
                                        required=False)

        self.required_args.add_argument('-g', '--group',
                                        nargs='+',
                                        dest="rg",
                                        help="Check group of RG is on one node",
                                        required=False)

    def verify_plugin_arguments(self):
        super(PluginHacmpRg, self).verify_plugin_arguments()

        if self.options.rg:
            # two arguments for -g
            if len(self.options.rg) < 2:
                self.unknown('argument -g should have two arguments at minimum !')

# Object Resource
class Resources(object):
    all=[]
    nodes = []
    collection = None

    def __init__(self,node,name_rg):
        self.node=node
        self.name=name_rg
        Resources.all.append(self)
        Resources.nodes.append(self.node)
        Resources.collection = Counter(Resources.nodes)

    @staticmethod
    def find_rg_node(rg):
        for r in Resources.all:
            if re.search(rg, r.name):
                return (r.node,r.name)

    def __repr__(self):
        return "Resources<Name: {}, Node: {}>".format(self.name,self.node)


oids = {
        'rg_name': '1.3.6.1.4.1.2.3.1.2.1.5.11.1.1.2',
        'rg_state': '1.3.6.1.4.1.2.3.1.2.1.5.11.3.1.3',
        'node_name': '1.3.6.1.4.1.2.3.1.2.1.5.2.1.1.4',
}

state = {
         2: 'online',
         4: 'offline',
         8: 'unknown',
         16: 'acquiring',
         32: 'releasing',
         64: 'error',
         256: 'onlineSec',
         1024: 'acquiringSec',
         4096: 'releasingSec',
         16384: 'errorsec',
         65536: 'offlineDueToFallover',
         131072: 'offlineDueToParentOff',
         262144: 'offlineDueToLackOfNode',
         524288: 'unmanaged',
         1048576: 'unmanagedSec',
         2097152: 'offlineDueToNodeForcedDown'
}

plugin = PluginHacmpRg(version=hacmp.__version__,
                       description="check statut of RG")

snmpquery = plugin.snmp.getnext(oids)

plugin.shortoutput = "All Resource Groups are online"

msg_err = "# ======= WARNING ========"
cmp = 0

try:
    # travel resource groups
    for result in snmpquery['rg_name']:
        logger.debug("oid {0.oid}, name {0.value}, index: {0.index}".format(result))

        online = False
        # travel resource group states
        for r in snmpquery['rg_state']:
            if r.oid.split('.')[-2] == str(result.index):
                node = [n.value for n in snmpquery['node_name'] if n.index == r.index][0]
                status = state[r.value]
                if status == 'online':
                    plugin.longoutput.insert(0, " {0.value} is {1} on {2}".format(result,status,node))
                    online = True
                    Resources(node, result.pretty())
                    break
                else:
                    online = False

        if online is False:
            cmp += 1
            msg_err += "{0} {1.value} is not online on any node".format('\n',result)
except:
    plugin.shortoutput = 'There was a problem during the processing of SNMP query results !'
    plugin.longoutput = list(traceback.format_exc())
    plugin.unknown(plugin.output())

if cmp > 0:
    if plugin.longoutput: plugin.longoutput.insert(0,'# ========== OK ==========')
    plugin.longoutput.insert(0, msg_err)
    plugin.shortoutput = "{} Ressource Group not online".format(cmp)
    plugin.warning(plugin.output())

if plugin.options.rg_alone:
    alone_node,alone_name = Resources.find_rg_node(plugin.options.rg_alone)

    if Resources.collection[alone_node] != 1:
        plugin.shortoutput = "Resource Group '{0}' is not alone on {1}".format(alone_name,alone_node)
        plugin.warning(plugin.output())

if plugin.options.rg:
    logger.debug(plugin.options.rg)
    node_def = Resources.find_rg_node(plugin.options.rg[0])[0]
    for r in plugin.options.rg:
        if node_def != Resources.find_rg_node(r)[0]:
            plugin.shortoutput = "Resource Groups {0} are not on same node".format(plugin.options.rg)
            plugin.warning(plugin.output())



plugin.ok(plugin.output())
