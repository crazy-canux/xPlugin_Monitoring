# service_informatica.cmd
#
# Check Informatica service on appservers, OK if 1 or 2 is running 
#

command[ wwfcsapp0010 ] = $PLUGINPATH$/sys/win/check_snmp_win_services.pl -H $HOST1$ -C $COMMUNITY$ -2 -n $MATCH$
command[ wwfcsapp0011 ] = $PLUGINPATH$/sys/win/check_snmp_win_services.pl -H $HOST2$ -C $COMMUNITY$ -2 -n $MATCH$

# Calculate results
state [ OK ] =  COUNT(OK) == 1
state [ WARNING ] =  COUNT(OK) > 2
state [ CRITICAL ] = COUNT(CRITICAL) == 2

