# worker_status_queue.cmd
#
# Check Monitoring Nagios/Gearman worker status queue, OK if 1 is running 
#

command[ monsat-master ] = $PLUGINPATH$/check_gearman -H $HOST1$ -q $QUEUE$ -s testcheck
command[ monsat-failover ] = $PLUGINPATH$/check_gearman -H $HOST2$ -q $QUEUE$ -s testcheck

# Calculate results
state [ OK ]        = COUNT(OK) == 1
state [ WARNING ]   = COUNT(OK) == 2
state [ CRITICAL ]  = COUNT(OK) == 0

