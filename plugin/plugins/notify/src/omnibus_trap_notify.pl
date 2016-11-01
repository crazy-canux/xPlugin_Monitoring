#!/usr/bin/perl -w
#
# sendtrap.pl: A script to send Nagios Service alerts.
#
# Modify the following as necessary for your local environment
#
# Changed by Michael FRANK, 7th June 2016
# Removed usage of configuration file and added the possibility to send traps to multiple trap receivers.
# Added the functionality to send messages to the system syslog.

use strict;
############ Modified: Michael FRANK 07.06.2016
use Sys::Syslog qw(:DEFAULT :standard :macros);
#############
#/home/frankm/develope/nagios-plugins/NotificationScript
#./src_omnibus_trap_notify.pl Alert testhost "My nice Service" 0 "Blubber" http://procedure http://graphlink "Bla Blubber Blubb" 10.10.10.10 Spacewalk MyNiceApp MyEnv

 
############ Modified: Michael FRANK 07.06.2016
#List of SNMP Trap receivers seperated by space
my @HOST_LIST = qw(10.20.106.73:1162 10.20.178.173:1162 10.20.179.127:1162 10.20.106.239:1162 10.20.106.240:1162);
# The final SNMP trap receiveiver from the HOST_LIST above
my $traprec;
# To hold the return string and exit code from Binary
my $output = "";
my $exitcode = 0;
############ End Modification MF ########################


my $snmpTrapCmd = "/usr/bin/snmptrap"; # Path to snmptrap, from http://www.net-snmp.org
my $OID = "1.3.6.1.4.1.20006.1"; # Object IDentifier for an alert, Nagios Enterprise OID is 20006

# default value
my $HOST_SNMP = "frselapp0021.sel.fr.corp";
my $PORT_SNMP = "162"; 
my $DEBUG = 0; 

#Number Arguments
my $nb = 12;
if (@ARGV < $nb) {
    print "\n\nERROR:  Number of Arguments is " . @ARGV . " but should be $nb\n";
    print "\nUsage: omnibus_trap_notify.pl NotifyType HostName SvcDesc ";
    print "SvcStateID SvcOutput SvcProcedureLink SvcGraphLink SvcLongOutput";
    print "HostAddress SatelliteName AppName EnvName\n\n";
    syslog ('err', "ERROR:  Number of Arguments is " . @ARGV . " but should be $nb\n") or warn "Could not write to log syslog: $!\n";
    exit (1);
} elsif (@ARGV > $nb) {
    syslog ('warning', "WARNING: Number of Arguments is " . @ARGV . " but should be $nb\n") or warn "Could not write to log syslog: $!\n";
}

# Parameters passed in from the alert.
# $1-$XX is the positional parameter list. $ARGV[0] starts at $1 in Perl.
my $nNotifyType = $ARGV[0];        # $1
my $nHostName = $ARGV[1];          # $2
my $nSvcDesc = $ARGV[2];           # $3
my $nSvcStateID = $ARGV[3];        # $4
my $nSvcOutput = $ARGV[4];         # $5
my $nSvcProcedureLink = $ARGV[5];  # $6
$ARGV[6] =~ s/srv=/&srv=/g;
my $nSvcGraphLink = $ARGV[6];      # $7
my $nSvcLongOutput = $ARGV[7];     # $8
my $nHostAddress = $ARGV[8];       # $9
my $nSatelliteName = $ARGV[9];     # $10
my $nAppName = $ARGV[10];          # $11
my $nEnvName = $ARGV[11];          # $12


# Arguments for cmd trap
my $cmd_args = qq/$OID '' 6 8 '' $OID.0 s "$nNotifyType" $OID.1 s "$nHostName" $OID.2 s "$nSvcDesc" $OID.3 i $nSvcStateID $OID.4 s "$nSvcOutput" $OID.5 s "$nSvcProcedureLink" $OID.6 s "$nSvcGraphLink" $OID.7 s "$nSvcLongOutput" $OID.8 s "$nHostAddress" $OID.9 s "$nSatelliteName" $OID.10 s "$nAppName" $OID.11 s "$nEnvName"  /;

# Test Donwtime
if ($nNotifyType eq "DOWNTIMEEND" or $nNotifyType eq "DOWNTIMECANCELLED" ) {
    if ($nSvcStateID != 0 ) {
        $nNotifyType = "PROBLEM";
    } else {
        syslog ('warning', "Not send trap because Service Downtime $nNotifyType and status Ok $nSvcStateID\n$cmd_args") or warn "Could not write to log syslog: $!\n" ;
        print  "\n#===== " . localtime() . " FIN Exec omnibus_trap_notify  =====\n" if $DEBUG;
        exit (0);
    }
} elsif ($nNotifyType eq "DOWNTIMESTART") {
    syslog ('warning', "Not send trap because Service Downtime $nNotifyType\n$cmd_args") or warn "Could not write to log syslog: $!\n" ;
    print "\n#===== " . localtime() . " FIN Exec omnibus_trap_notify  =====\n" if $DEBUG;
    exit (0);
}

#my $cmd_p = qq/$snmpTrapCmd -v 1 -c public $hostPortSNMP $cmd_args/;

#print "CMD : $cmd_p\n" or die "Could write to log file $file_log: $!\n";

# Debug
if ($DEBUG) {
    print "#===== DEBUG MODE=====\n";
    print " Host                         : $HOST_SNMP\n";
    print " Port                         : $PORT_SNMP\n";
    print " ARGS\n ----\n";
    print "  NotifyType                  : $nNotifyType\n";
    print "  HostName                    : $nHostName\n";
    print "  SvcDesc                     : $nSvcDesc\n";
    print "  SvcStateID                  : $nSvcStateID\n";
    print "  SvcOutput                   : $nSvcOutput\n";
    print "  SvcProcedureLink            : $nSvcProcedureLink\n";
    print "  SvcGraphLink                : $nSvcGraphLink\n";
    print "  SvcLongOutput               : $nSvcLongOutput\n";
    print "  Hostaddress                 : $nHostAddress\n";
    print "  SatelliteName               : $nSatelliteName\n";
    print "  AppName                     : $nAppName\n";
    print "  EnvName                     : $nEnvName\n";
}

############ Modified: Michael FRANK 07.06.2016
# send trap # 
#my $code_retour = system($cmd_p);
#
# Go through the list of hosts defined in @HOST_LIST and send for each element in the array a SNMP trap. Send error to syslog if the command fails with returning an error message.

foreach $traprec (@HOST_LIST){

   # run the SNMP trap sending command in the background and send STDOUT and STDERR to $output
   # This will fork teh ANMP trap command from the script so that the script is not blocked if the command fails.
   $output = `$snmpTrapCmd -v 1 -c public $traprec $cmd_args 2>&1 >/tmp/snmp.pid &`;
   
   # If trap sending command does not exit with 0 we send error message to syslog else we send to success to syslog
   if ( $output ne "" )
     {
        syslog ('err',"Failed sending Notification to $traprec for host $nHostName and service $nSvcDesc: $! : $output \n") or warn "Could not write to log syslog: $!\n";
        $exitcode = 1;
        $output = "";
     }
     else
     {
        if ($DEBUG) {syslog('info', "Send Notification to $traprec for host $nHostName and service $nSvcDesc %d $output",$? >> 8 ) or warn "Could not write to log syslog: $!\n"};
        $output = "";
     }
};

#Close Syslog
closelog();
exit $exitcode;
############ End Modification MF ########################

