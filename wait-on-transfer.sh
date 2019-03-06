#!/bin/bash

# PREREQUISITES
#
# The Globus CLI must be installed and have an active login session.
#

# DESCRIPTION
#
# Blocks on active transfers
# Usage: ./wait-on-transfer.sh <UUID of transfer task>
#
# Set verbose to "true" for regular output
# Set wait_seconds for interval between status checks


verbose="true"
wait_seconds=10

if [ -z ${1+x} ]
then
    echo "Usage: ./wait-on-transfer.sh <UUID of transfer task>"
    exit 1
fi

transfer_id=$1

echo "Checking status of transfer $transfer_id"

transfer_status=$(globus task show --format json --jmespath 'status' $transfer_id | tr -d '"')
while [ "$transfer_status" = "ACTIVE" ]
do
    if [ "$verbose" = "true" ]
    then
        echo "Transfer is active, waiting"
    fi
    sleep $wait_seconds
    transfer_status=$(globus task show --format json --jmespath 'status' $transfer_id | tr -d '"')
done

echo "Transfer status is $transfer_status"
