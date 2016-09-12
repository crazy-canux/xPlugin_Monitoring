# hacmp_two_nodes_status.cmd
#
# Check global state of a HACMP cluster with 2 nodes
# Author: Vincent BESANCON <vincent.besancon@faurecia.com>
#

command[ substate ] = $PLUGINPATH$/check_snmp -H $HOSTIP$ -C $COMMUNITY$ -m '/usr/share/mibs/site/HACMP.txt' -o RISC6000CLSMUXPD-MIB::clusterSubState.$HACMP_CLUSTER_ID$ -l 'Cluster_substate' -s 'stable(32)'
command[ node_primary ] = $PLUGINPATH$/check_snmp -H $HOSTIP$ -C $COMMUNITY$ -m '/usr/share/mibs/site/HACMP.txt' -o RISC6000CLSMUXPD-MIB::nodeState.$HACMP_PROD_NODE_ID$ -l "Node_Primary" -s "up(2)"
command[ node_secondary ] = $PLUGINPATH$/check_snmp -H $HOSTIP$ -C $COMMUNITY$ -m '/usr/share/mibs/site/HACMP.txt' -o RISC6000CLSMUXPD-MIB::nodeState.$HACMP_BCKP_NODE_ID$ -l "Node_Secondary" -s "up(2)"
command[ ressource_node_pri ] = $PLUGINPATH$/check_snmp -H $HOSTIP$ -C $COMMUNITY$ -m '/usr/share/mibs/site/HACMP.txt' -o RISC6000CLSMUXPD-MIB::resGroupNodeState.$HACMP_RESOURCE_GRP_ID$.$HACMP_PROD_NODE_ID$ -w 2 -l "Resource_Node_Pri"
command[ ressource_node_sec ] = $PLUGINPATH$/check_snmp -H $HOSTIP$ -C $COMMUNITY$ -m '/usr/share/mibs/site/HACMP.txt' -o RISC6000CLSMUXPD-MIB::resGroupNodeState.$HACMP_RESOURCE_GRP_ID$.$HACMP_BCKP_NODE_ID$ -w 2 -l "Resource_Node_Sec"


# Calculate results
state [ OK ] =  COUNT(OK) >= 4
state [ WARNING ] =  (1==0)
state [ CRITICAL ] = ressource_node_pri == WARNING && ressource_node_sec == WARNING || COUNT(CRITICAL) > 0
