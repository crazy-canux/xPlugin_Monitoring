#!/usr/bin/php -q
<?php
/*
 * Nagios_Plugins
 * 
 * $CVSHeader: Nagios_Plugins/check_aix_disks.php,v 1.4 2006/09/19 12:45:24 mkuehn Exp $
 * 
 * Created on Sep 19, 2006 by mkuehn (marcel@kuehns.org)
 * License: GPL
 * No warranties in any way given.
 * 
 * $Log: check_aix_disks.php,v $
 * Revision 1.4  2006/09/19 12:45:24  mkuehn
 * verified working with 5.3
 * verified NOT working with 4.3
 *
 * Revision 1.3  2006/09/19 12:41:58  mkuehn
 * added error message if no disks are found.
 *
 * Revision 1.2  2006/09/19 12:36:12  mkuehn
 * removed the linebreaks in the output messages.
 *
 * Revision 1.1  2006/09/19 12:02:23  mkuehn
 * CVS Repository Changes.
 *
 * Description:
 * OK this works via SNMP and comes with different restrictions. 
 * 1) I am not able to distinct between harddisks in the AIX itself (system disks) 
 * and storage attached harddisks.
 * 2) I cannot say which harddisk is which /mountpoint. For some reason IBM 
 * doesn't have a LINK between the logical and the physical volume which i can get
 * via SNMP lookups.
 * 3) Verified working with AIX 5.3, NOT working with 4.3
 */

require_once("/usr/lib/Company/plugins/utils.php");

if(!$argv[2]){
	print("\nUsage: ./check_aix_disks <communityname> <host>");
	die();
}
#print_r($argv);
if(ereg("[a-z0-9\-]{1,30}",$argv[1])){
	$community	=	$argv[1];
}
if($argv[2]){
	$hostname	=	$argv[2];
}

$cmd			=	SNMPWALK." -c $community -v1 $hostname ";
#get devices
$dev_cmd		=	$cmd . "hrDiskStorageMedia -O qut";
#get status
$dev_status_cmd	=	$cmd . "hrDeviceStatus -O qut";

$result_dev		=	shell_exec($dev_cmd);
$result_stat	=	shell_exec($dev_status_cmd);

$result_by_line	=	explode("\n",$result_dev);
if(!is_array($result_by_line)){
	echo "UNKNOWN: no disks found.";
	exit(STATE_UNKNOWN);
	die();
}
foreach($result_by_line as $index => $value){
	if(ereg("^host.hrDevice.hrDiskStorageTable.hrDiskStorageEntry.hrDiskStorageMedia.([0-9]{1,3}) (hardDisk)",$value,$regs)){
		$disks++;
		#print_r($regs);
		$dev_id		=	$regs[1];
		$dev_type	=	strtolower($regs[2]);
		$dev_arr[$dev_id]["type"]	=	$dev_type;
		unset($dev_id);unset($dev_type);		
	}
}
if(!$disks){
	#only tested with AIX 5.3
	echo "UNKNOWN: no disks found.";
	exit(STATE_UNKNOWN);
	die();
}
$result_by_line	=	explode("\n",$result_stat);
foreach($result_by_line as $index => $value){
	if(ereg("^host.hrDevice.hrDeviceTable.hrDeviceEntry.hrDeviceStatus.([0-9]{1,3}) ([a-zA-Z0-9]{1,20})",$value,$regs)){
		#print_r($regs);
		$dev_id		=	$regs[1];
		$dev_status	=	strtolower($regs[2]);
		if($dev_arr[$dev_id]){
				$dev_arr[$dev_id]["status"]	=	$dev_status;
		}
	}
	
}
foreach($dev_arr as $dev_id => $value){
	if($dev_arr[$dev_id]["status"] == 'unknown'){
		$unknown[]	=	$dev_id;
	}
	elseif($dev_arr[$dev_id]["status"] == 'warning'){
		$warnung[]	=	$dev_id;
	}
	elseif($dev_arr[$dev_id]["status"] == 'testing'){
		$testing[]	=	$dev_id;
	}
	elseif($dev_arr[$dev_id]["status"] == 'down'){
		$down[] 	=	$dev_id;
	}
	elseif($dev_arr[$dev_id]["status"] == 'running'){
		$OK[]			=	$dev_id;
	}
}
if(is_array($down)){
	echo "CRITICAL: harddisk(s) down : (".count($down)."/$disks).";
	exit(STATE_CRITICAL);
	die();
}
elseif(is_array($warnung) || is_array($testing)){
	echo "WARNING: harddisk(s) in WARNING or TESTING state: (";
	print(count($warnung) + count($testing));
	echo "/$disks).";
	exit(STATE_WARNING);
	die();
}
elseif(is_array($unknown)){
	echo "UNKNOWN: harddisk(s) report no or unknown state: (".count($unknown)."/$disks).";
	exit(STATE_UNKNOWN);
	die();
}
else{
	echo "OK: harddisk(s) reporting OK state: (".count($OK)."/$disks).";
	exit(STATE_OK);
	die();
}
?>
