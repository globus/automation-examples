#!/bin/bash

# This script will submit a transfer request that does
# a recursive sync. Options (endpoints, paths, sync type)
# are configured below.

# TODO: add lockfile implementation

# Convenience functions

# always start unset
unset abort_message

# start with default of 0
rc=0

# Abort with message
function abort () {
    echo "$abort_message" >&2
    exit $rc
}

# Check if abort is necessary, and if so do it
function check_rc () {
    if [ $# -gt 0 ];
    then
        abort_message="$1"
    fi

    if [ $rc -ne 0 ];
    then
        abort
    fi
}

# Check if abort is necessary, fetching rc first
function check_last_rc () {
    # must be the first command of the function
    rc=$?
    check_rc "$@"
}

# LOCKFILE='/tmp/cli-sync.lock'
LAST_TRANSFER_ID_FILE='last-transfer-id.txt'

# Globus Tutorial Endpoint 1
source_endpoint='ddb59aef-6d04-11e5-ba46-22000b92c6ec'

# Globus Tutorial Endpoint 2
destination_endpoint='ddb59af0-6d04-11e5-ba46-22000b92c6ec'

# Sample data
source_path='/share/godata/'

# Destination Path
# The directory will be created if it doesn't exist
destination_path='/~/sync-demo/'

# Sync option
# Choices are
#   exists   TODO: add description
#   size     TODO: add description
#   mtime    TODO: add description
#   checksum TODO: add description
synctype='checksum'

# Only contine if the previous transfer succeeded or failed
# Other statuses will mean that previous transfer is either still
# running, or require human intervention (e.g., PAUSED)
if [ -e "$LAST_TRANSFER_ID_FILE" ]
then
    last_transfer_id=$(cat "$LAST_TRANSFER_ID_FILE")
    last_transfer_status=$(globus task show --format json --jmespath 'status' $last_transfer_id | tr -d '"')
    if [ "$last_transfer_status" != "SUCCEEDED" ] && [ "$last_transfer_status" != "FAILED" ]
       then
           abort_message="Last transfer $last_transfer_id status is $last_transfer_status, aborting"
           rc=1
           abort
    fi
fi

# Verify that the source paths is a directory
globus ls --format json --jmespath 'code' "$source_endpoint:$source_path" >& /dev/null
check_last_rc "Could not list source directory"

# Submit sync transfer, get the task ID
globus_output=$(globus transfer --format json --jmespath 'task_id'  --recursive \
                       --delete --sync-level $synctype \
                       "$source_endpoint:$source_path" \
                       "$destination_endpoint:$destination_path")

# Check status
check_last_rc "Globus transfer submission failed"

# Save ID of new sync transfer
echo $globus_output | tr -d '"' > "$LAST_TRANSFER_ID_FILE"

# rm -f $LOCKFILE
