#!/bin/bash

PURL=${1}
PJSESSIONID=${2}
PUSER=${3}
PPASSWORD=${4}
TIMEOUT=${5-30}
DIRECTORY=`dirname $0`;

timeout ${TIMEOUT} java -cp $DIRECTORY LoadBalancingCheck "${PURL}" "${PJSESSIONID}" "${PUSER}" "${PPASSWORD}" "1" $@ 2>&1

RETVAL=$?
if [ $RETVAL -eq 124 ]
then
    echo "CRITICAL - Unable to simulate a login for this host within ${TIMEOUT} seconds !"
    exit 2
fi

exit $RETVAL
