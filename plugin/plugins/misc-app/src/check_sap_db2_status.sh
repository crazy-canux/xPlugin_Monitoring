#!/bin/bash
#
# Nagios External Command Action
# ------------------------------
#
# Plugin: check_sap_db2_status
# Description: Shell script wrap the command output of 'check_sap_db2_status' nagios
#              command and format a good result.
#
# Author: Vincent BESANCON <vincent.besancon@faurecia.com>
# SVN: $Id: check_sap_db2_status.sh 781 2012-02-23 10:28:02Z bailat $
#

# Usage
if [ $# -lt 3 ]; then
        echo "Usage: `basename $0` <host_name> <db2_user> <db2_instance>"
        exit 1
fi

# Args
HOST_NAME=$1
DB2_USER=$2
DB2_INSTANCE=$3

# Output & return code
OUTPUT=`ssh -q -t $HOST_NAME "sudo -u $DB2_USER -i /usr/local/nagios/libexec/check_db2.sh $DB2_INSTANCE"`
RETURN_CODE=$?


if [ $RETURN_CODE -eq 3 ]; then
        echo "UNKNOWN - DB2 Status is not available !"
        exit 3
fi

if [ $RETURN_CODE -gt 0 ]; then
	echo "ALERT - DB2 is unavailable !"
	exit 2
fi

echo "OK - DB2 is available"
exit 0
