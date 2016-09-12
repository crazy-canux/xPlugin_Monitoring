# process_elim_on_master.cmd
#
# Check ELIM processes on Nemo Masters, OK if 3 are running on a master.
#

command[ ctm0001 ] = $PLUGINPATH$/sys/common/check_snmp_process.pl -H $MASTER_LSF1$ -C $COMMUNITY$ -2 -t 60 -n $PROCESS_MATCH$ -w2 -c2
command[ ctm0002 ] = $PLUGINPATH$/sys/common/check_snmp_process.pl -H $MASTER_LSF2$ -C $COMMUNITY$ -2 -t 60 -n $PROCESS_MATCH$ -w2 -c2
command[ ctm0003 ] = $PLUGINPATH$/sys/common/check_snmp_process.pl -H $MASTER_LSF3$ -C $COMMUNITY$ -2 -t 60 -n $PROCESS_MATCH$ -w2 -c2

# Calculate results
state [ OK ] =  COUNT(OK) == 1
state [ WARNING ] =  COUNT(OK) > 1
state [ CRITICAL ] = COUNT(CRITICAL) == 3

