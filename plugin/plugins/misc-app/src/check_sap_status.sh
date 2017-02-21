#!/bin/bash
#
# Nagios External Command Action
# ------------------------------
#
# Plugin: check_sap_status
# Description: Shell script wrap the command output of 'check_sap_status' nagios
#              command and format a good result.
#
# Author: Canux CHENG <canuxcheng@gmail.com>
# SVN: $Id: check_sap_status.sh 835 2012-10-26 13:48:09Z  $
#

# Usage
if [ $# -lt 2 ]; then
        echo "Usage: `basename $0` <host_name> <sap_user>"
        exit 3
fi

# Args
HOST_NAME=$1
SAP_USER=$2

# Output & return code
OUTPUT=`ssh -q -t $HOST_NAME "sudo -u $SAP_USER -i /usr/local/nagios/libexec/check_sap.sh"`
RETURN_CODE=$?
if [ $RETURN_CODE -eq 3 ]; then
        echo "UNKNOWN - A check is already in progress !"
        exit 3
fi

if [ $RETURN_CODE -gt 0 ]; then
	echo "ALERT - SAP is unavailable !"
	exit 2
fi

echo "OK - SAP is available"
exit 0
