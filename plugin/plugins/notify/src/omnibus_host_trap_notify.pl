#!/usr/bin/perl -w
#
# sendtrap.pl: A script to send Nagios Host alerts.
#
# Modify the following as necessary for your local environment
#
use strict;
use Config::Simple;

# FOR TEST
#my $file_conf = "/tmp/omnibus.cfg";
#my $file_log = "/tmp/nagios_omnibus_host_notify.log";

my $file_conf = "/etc/nagios/omnibus.cfg";
my $file_log = "/var/log/nagios/omnibus_host_trap_notify.log";
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
print LogFile  "\n\n#===== " . localtime() . " Exec omnibus_host_trap_notify =====\n";

#Number Arguments
my $nb = 11;
if (@ARGV < $nb) {
    print "ERROR:  Number of Arguments " . @ARGV . " < $nb\n";
    print LogFile "ERROR:  Number of Arguments " . @ARGV . " < $nb\n";
    print "\n Usage: omnibus_host_trap_notify.pl HostNotifyType HostName ";
    print "HostAlias HostStateID HostOutput HostProcedureLink HostAddress ";
    print "SatelliteName HostGroupAlias AppName EnvName\n";
    close LogFile;
    exit (1);
} elsif (@ARGV > $nb) {
    print LogFile "ERROR: Number of Arguments " . @ARGV . " > $nb\n";
    print LogFile " Arguments: ", join(";",@ARGV), "\n\n";
}


my $hostPortSNMP = $HOST_SNMP . ":" . $PORT_SNMP;

# Parameters passed in from the alert.
# $1-$XX is the positional parameter list. $ARGV[0] starts at $1 in Perl.
my $nHostNotifyType = $ARGV[0];    # $1
my $nHostName = $ARGV[1];          # $2
my $nHostAlias = $ARGV[2];         # $3
my $nHostStateID = $ARGV[3];       # $4
my $nHostOutput = $ARGV[4];        # $5
my $nHostProcedureLink = $ARGV[5]; # $6
my $nHostAddress = $ARGV[6];       # $7
my $nSatelliteName = $ARGV[7];     # $8
my $nHostGroupAlias = $ARGV[8];    # $9
my $nAppName = $ARGV[9];           # $10
my $nEnvName = $ARGV[10];          # $11

# Arguments for cmd trap
my $cmd_args = qq/$OID '' 6 6 '' $OID.0 s "$nHostNotifyType" $OID.1 s "$nHostName" $OID.2 s "$nHostAlias" $OID.3 i $nHostStateID $OID.4 s "$nHostOutput" $OID.5 s "$nHostProcedureLink" $OID.6 s "$nHostAddress" $OID.7 s "$nSatelliteName" $OID.8 s "$nHostGroupAlias" $OID.9 s "$nAppName" $OID.10 s "$nEnvName"  /;

# Test Donwtime
if ($nHostNotifyType eq "DOWNTIMEEND" or $nHostNotifyType eq "DOWNTIMECANCELLED" ) {
    if ($nHostStateID != 0 ) {
        $nHostNotifyType = "PROBLEM";
    } else {
        print LogFile "\nNot send trap because Downtime $nHostNotifyType and status Ok $nHostStateID\n$cmd_args";
        print LogFile "\n#===== " . localtime() . " FIN Exec omnibus_host_trap_notify  =====\n";
        close LogFile;
        exit (0);
    }
} elsif ($nHostNotifyType eq "DOWNTIMESTART") {
    print LogFile "\nNot send trap because Downtime $nHostNotifyType\n$cmd_args";
    print LogFile "\n#===== " . localtime() . " FIN Exec omnibus_host_trap_notify  =====\n";
    close LogFile;
    exit (0);
}


# Prepare Send Trap
my $cmd_p = qq/$snmpTrapCmd -v 1 -c public $hostPortSNMP $cmd_args/;
print LogFile "CMD : $cmd_p\n";

# Debug
if ($DEBUG){
    print LogFile "#===== DEBUG MODE=====\n";
    print LogFile " Host                        : $HOST_SNMP\n";
    print LogFile " Port                        : $PORT_SNMP\n";
    print LogFile " ARGS\n ----\n";
    print LogFile "  HostNotifyType             : $nHostNotifyType\n";
    print LogFile "  HostName                   : $nHostName\n";
    print LogFile "  HostAlias                  : $nHostAlias\n";
    print LogFile "  HostStateID                : $nHostStateID\n";
    print LogFile "  HostOutput                 : $nHostOutput\n";
    print LogFile "  HostProcedureLink          : $nHostProcedureLink\n";
    print LogFile "  HostAddress                : $nHostAddress\n";
    print LogFile "  SatelliteName              : $nSatelliteName\n";
    print LogFile "  HostGroupAlias             : $nHostGroupAlias\n";
    print LogFile "  AppName                    : $nAppName\n";
    print LogFile "  EnvName                    : $nEnvName\n";
}

# send trap
my $code_retour = system($cmd_p);
print LogFile  "\n#===== " . localtime() . " FIN Exec omnibus_host_trap_notify ($code_retour) =====\n";
close LogFile;
exit (0);
