#!/bin/bash

# PREREQUISITES
#
# The Globus CLI must be installed and have an active login session.
#

# DESCRIPTION
#
# Blocks on active transfers
# Usage: ./wait-on-transfer.sh <UUID of transfer task> <optional max wait seconds>
#
# Set verbose to "true" for regular output
# Set wait_seconds for interval between status checks

verbose="true"
wait_seconds=10
current_wait=0
max_wait=1

if [ -z ${1+x} ]
then
    echo "Usage: ./wait-on-transfer.sh <UUID of transfer task> <optional max wait seconds>"
    exit 1
else
    transfer_id=$1
fi

if [ -z ${2+x} ]
then
    max_wait_interval=-1
else
    max_wait=$2
    max_wait_interval=$wait_seconds
fi

echo "Checking status of transfer $transfer_id"

transfer_status=$(globus task show --format json --jmespath 'status' $transfer_id | tr -d '"')

while [ "$transfer_status" = "ACTIVE" ]
do
    if [ "$verbose" = "true" ]
    then
        echo "Transfer is active, waiting"
    fi
    sleep $wait_seconds
    let "current_wait += $max_wait_interval"
    if [ "$max_wait" -lt $current_wait ]
    then
        echo "Maximum wait time of $max_wait seconds exceeded, transfer is still ACTIVE"
        exit 1
    fi
       
    transfer_status=$(globus task show --format json --jmespath 'status' $transfer_id | tr -d '"')
done

if [ "$transfer_status" != "SUCCEEDED" ]
then
    echo "Transfer has stopped with status $transfer_status"
    exit 1
fi

echo "Transfer completed, status is $transfer_status"
exit 0
