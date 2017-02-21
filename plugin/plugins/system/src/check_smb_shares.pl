#! /usr/bin/perl -w
#
# check_smb_shares.pl - nagios plugin 
# 
#
# Copyright (C) 2004 Gerd Mueller / Netways GmbH
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#

use POSIX;
use strict;
use lib "/usr/lib/canux/plugins"  ;
use Filesys::SmbClient; 

use Data::Dumper;

my %ERRORS = ('UNKNOWN'  => '3',
              'OK'       => '0',
              'WARNING'  => '1',
              'CRITICAL' => '2');


use Getopt::Long;
Getopt::Long::Configure('bundling');

my $opt_c=2;
my $opt_w=1;
my $opt_h;
my $opt_n;
my $opt_t;
my $service;
my $recursive=0;

my $status;
my $hostname;
my $args;
my $user;
my $password;
my $domain;

my $PROGNAME = "check_hopcount";


$status = GetOptions(
		"h"   => \$opt_h, "help"       => \$opt_h,
		"c=s" =>\$opt_c,
		"w=s" =>\$opt_w,
		"n"   =>\$opt_n,
		"t"   =>\$opt_t,
		"r"   => \$recursive,
		"U=s" => \$user, "user=s" => \$user,		
		"P=s" => \$password, "password=s" => \$password,		
		"D=s" => \$domain, "domain=s" => \$domain,		
		"H=s" => \$hostname, "hostname=s" => \$hostname,		
		"A=s" => \$args, "args=s" => \$args,		
		"S=s" => \$service, "service=s" => \$service);		

if($opt_h || !$hostname || !$service) {
	print_usage() ;
}

my $rw=0;

my $errorcode = $ERRORS{'OK'};
my $output="";
my $names="";
my $dummy;
my $perfdata=1;

my $smb = new Filesys::SmbClient(username  => $user,password  => $password,workgroup => $domain);

if($smb) {
	
	SWITCH: for ($service) {
		(/Filecount/i || /Foldersize/i) && do {
			my $files=0;
			my $dirs=0;
			my $links=0;
			my $size=0;
			my $tsize="";
			my $units="";
			my $s;
			($output,$errorcode,$files,$dirs,$links,$size)=count_files($recursive,$hostname,$args,$files,$dirs,$links,$size,$errorcode);
			
			if($opt_t) {
				$tsize = $size;
				if($tsize>1024) { $tsize/=1024;$units="KB";}
				if($tsize>1024) { $tsize/=1024;$units="MB";}
				if($tsize>1024) { $tsize/=1024;$units="GB";}
				if($tsize>1024) { $tsize/=1024;$units="TB";}
				$tsize=sprintf("%.2lf %s",$tsize,$units);
			}
			
			#$size = POSIX::ceil($size);
			
			if($service =~ m/Filecount/i) {
				$rw=$files+$dirs+$links;
				$s="s" if($rw!=1);
				$output=$rw." Item".$s." ($dirs Directorys, $files Files, $links Links, ".($size)." ) in smb://$hostname/$args" if($output eq "");
			} else {
				$rw=$size;
				$output=$tsize." ($dirs Directories, $files Files, $links Links) in smb://$hostname/$args" if($output eq "");
			}
			last SWITCH;
		};
		(/Writeable/i) && do {
			$perfdata=0;
			 my $fd = $smb->open(">smb://$hostname/$args", 0666);
			 if($fd) {
			 	$smb->close($fd);
			 	$smb->unlink("smb://$hostname/$args");
			 	$errorcode=$ERRORS{'OK'};
			 	$output.="smb://$hostname/$args ist writeable";
			 }  else {
			 	$errorcode=$ERRORS{'CRITICAL'};
			 	$output.="smb://$hostname/$args is not writeable (\"".$!."\").";
			 }
			last SWITCH;
		};
		$output ='No known service type to check! \n ';
		$errorcode = $ERRORS{'UNKNOWN'};
	}
    
    if($opt_c ne "" && $rw>=$opt_c && $errorcode != $ERRORS{'UNKNOWN'}) {
    	$errorcode = $ERRORS{'CRITICAL'};
    } elsif($rw>=$opt_w) {
    	$errorcode = $ERRORS{'WARNING'};
    } 
    $output.= " | '$service'=".$rw.";".$opt_w.";".$opt_c if($perfdata);
    $output.= "\n";
	
}
else {
	$output ='smb connect to $hostname failed ("'.$!.'")! \n ';
	$errorcode = $ERRORS{'UNKNOWN'};
}

print $output;
exit $errorcode;


sub print_usage {
	printf "\n";
	printf "check_smb_shares.pl -S <Service> [-U <User>] [-P <Password>] [-D <Domain>] -H <Hostname> -A <Directory/Share> -w n -c n [-r] [-t]\n";
	printf "Service can be:\n";
	print " - FILECOUNT: Counts files in a particular directory/share (ARGS) \n";
	print "      check_smb.pl -S FILECOUNT -A /Windows/Temp -U foo -P bar -D fooBar -w 10 -c 20\n";
	print " - FOLDERSIZE: Counts bytes used in a particular directory/share (ARGS) \n";
	print " - WRITEABLE:  Checks if a particular file (ARGS) can be stored on the share/directory\n\n";
	print "Options:\n";
	print "-t\tTranslate like df -h\n";
	print "-r\tRecursive\n";
	printf "\nCopyright (C) 2004 Gerd Mueller / Netways GmbH\n";
	printf "\n\n";
	exit $ERRORS{"UNKNOWN"};
}

sub count_files {
	my $output="";
	my ($recursive,$hostname,$args,$files,$dirs,$links,$size,$errorcode) = @_;
	# print $args."\n";
	my $fd = $smb->opendir("smb://$hostname/$args");
	if($fd) {
		while (my $f = $smb->readdir_struct($fd)) {
			# print Dumper \%$f;
 			if($f->[0]==SMBC_FILE) {
  				$files++;
  				my @stats = $smb->stat("smb://$hostname/$args/".$f->[1]);
  				$size+=$stats[7];
  			} elsif ($f->[0]==SMBC_DIR) {
  				if($f->[1] ne "." && $f->[1] ne "..") {
  					$dirs++;
  					($output,$errorcode,$files,$dirs,$links,$size)=count_files($recursive,$hostname,$args."/".$f->[1],$files,$dirs,$links,$size,$errorcode) if($recursive);
  				}
  			} elsif ($f->[0]==SMBC_LINK) {
  				$links++;
  			}
		}
  		$smb->closedir($fd);
	} else  {
		$output = 'directory smb://'.$hostname.'/'.$args.' does not exist';
		$errorcode = $ERRORS{'UNKNOWN'};		
	}
	return ($output,$errorcode,$files,$dirs,$links,$size);
}
