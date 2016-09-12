#!/usr/bin/perl -w
#
# sendtrap.pl: A script to send Nagios Service alerts.
#
# Modify the following as necessary for your local environment
#

use strict;
use Config::Simple;

# FOR TEST
#my $file_conf = "/tmp/omnibus.cfg";
#my $file_log = "/tmp/omnibus_trap_notify.log";

my $file_conf = "/etc/nagios/omnibus.cfg";
my $file_log = "/var/log/nagios/omnibus_trap_notify.log";
my $snmpTrapCmd = "/usr/bin/snmptrap"; # Path to snmptrap, from http://www.net-snmp.org
my $OID = "1.3.6.1.4.1.20006.1"; # Object IDentifier for an alert, Nagios Enterprise OID is 20006

# default value
my $HOST_SNMP = "frselapp0021.sel.fr.corp"; 
my $PORT_SNMP = "162"; 
my $DEBUG = 0; 

# Read file conf
if (-f $file_conf){
    my $cfg = Config::Simple->new($file_conf);
    $DEBUG = $cfg->param("debug") if $cfg->param("debug");
    $HOST_SNMP = $cfg->param("snmp.host") if $cfg->param("snmp.host");
    $PORT_SNMP = $cfg->param("snmp.port") if $cfg->param("snmp.port");
}

open (LogFile,">> $file_log"); 
print LogFile  "\n\n#===== " . localtime() . " Exec omnibus_trap_notify =====\n";

#Number Arguments
my $nb = 12;
if (@ARGV < $nb) {
    print "ERROR:  Number of Arguments " . @ARGV . " < $nb\n";
    print LogFile "ERROR:  Number of Arguments " . @ARGV . " < $nb\n";
    print "\n Usage: omnibus_trap_notify.pl NotifyType HostName SvcDesc ";
    print "SvcStateID SvcOutput SvcProcedureLink SvcGraphLink SvcLongOutput ";
    print "HostAddress SatelliteName AppName EnvName\n";
    close LogFile;
    exit (1);
} elsif (@ARGV > $nb) {
    print LogFile "ERROR: Number of Arguments " . @ARGV . " > $nb\n";
    print LogFile " Arguments: ", join(";",@ARGV), "\n\n";
}


my $hostPortSNMP = $HOST_SNMP . ":" . $PORT_SNMP;


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
        print LogFile "\nNot send trap because Service Downtime $nNotifyType and status Ok $nSvcStateID\n$cmd_args";
        print LogFile "\n#===== " . localtime() . " FIN Exec omnibus_trap_notify  =====\n";
        close LogFile;
        exit (0);
    }
} elsif ($nNotifyType eq "DOWNTIMESTART") {
    print LogFile "\nNot send trap because Service Downtime $nNotifyType\n$cmd_args";
    print LogFile "\n#===== " . localtime() . " FIN Exec omnibus_trap_notify  =====\n";
    close LogFile;
    exit (0);
}


# Prepare Send Trap
my $cmd_p = qq/$snmpTrapCmd -v 1 -c public $hostPortSNMP $cmd_args/;
print LogFile "CMD : $cmd_p\n";



# Debug
if ($DEBUG) {
    print LogFile "#===== DEBUG MODE=====\n";
    print LogFile " Host                         : $HOST_SNMP\n";
    print LogFile " Port                         : $PORT_SNMP\n";
    print LogFile " ARGS\n ----\n";
    print LogFile "  NotifyType                  : $nNotifyType\n";
    print LogFile "  HostName                    : $nHostName\n";
    print LogFile "  SvcDesc                     : $nSvcDesc\n";
    print LogFile "  SvcStateID                  : $nSvcStateID\n";
    print LogFile "  SvcOutput                   : $nSvcOutput\n";
    print LogFile "  SvcProcedureLink            : $nSvcProcedureLink\n";
    print LogFile "  SvcGraphLink                : $nSvcGraphLink\n";
    print LogFile "  SvcLongOutput               : $nSvcLongOutput\n";
    print LogFile "  Hostaddress                 : $nHostAddress\n";
    print LogFile "  SatelliteName               : $nSatelliteName\n";
    print LogFile "  AppName                     : $nAppName\n";
    print LogFile "  EnvName                     : $nEnvName\n";
}

# send trap
my $code_retour = system($cmd_p);
print LogFile  "\n#===== " . localtime() . " FIN Exec omnibus_trap_notify ($code_retour) =====\n";
close LogFile;
exit (0);
