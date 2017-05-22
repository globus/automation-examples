#!/bin/bash

# Sync one folder with another, across two endpoints.
# The sync will recurse through all subdirectories.
# Default values are below:

# Source: Globus Tutorial Endpoint 1: /share/godata
# Destination: Globus Tutorial Endpoint 2: /~/sync-demo/ # Your account home directory

# Visit https://www.globus.org/app/transfer?destination_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
# to view the transferred data.


# Options (endpoints, paths, sync type)
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

    if [ $rc -eq 0 -a "$2" != "" ];
    then
        printf "$2"
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
SOURCE_ENDPOINT='ddb59aef-6d04-11e5-ba46-22000b92c6ec'

# Globus Tutorial Endpoint 2
DESTINATION_ENDPOINT='ddb59af0-6d04-11e5-ba46-22000b92c6ec'

# Sample data
SOURCE_PATH='/share/godata/'

# Destination Path
# The directory will be created if it doesn't exist
DESTINATION_PATH='/~/sync-demo/'

# Sync options:
#   exists   Copy files that do not exist at the destination.
#   size     Copy files if the size of the destination does not match the size of the source.
#   mtime    Copy files if the timestamp of the destination is older than the timestamp of the source.
#   checksum Copy files if checksums of the source and destination do not match. Files on the destination are never deleted.
# For more information:
# $ globus transfer --help
# < OR >
# https://docs.globus.org/api/transfer/task_submit/#transfer_and_delete_documents
SYNCTYPE='checksum'

# Only continue if the previous transfer succeeded or failed
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
globus ls --format json --jmespath 'code' "$SOURCE_ENDPOINT:$SOURCE_PATH" >& /dev/null
check_last_rc "Could not list source directory"

# Submit sync transfer, get the task ID
GLOBUS_OUTPUT=$(globus transfer --format json --jmespath 'task_id'  --recursive \
                       --delete --sync-level $SYNCTYPE \
                       "$SOURCE_ENDPOINT:$SOURCE_PATH" \
                       "$DESTINATION_ENDPOINT:$DESTINATION_PATH")

SUC_MSG="Started sync from $SOURCE_PATH to $DESTINATION_PATH"
# Note the double percent signs and \n for the printf statement
LINK="Link:\nhttps://www.globus.org/app/transfer?destination_id=${DESTINATION_ENDPOINT}&destination_path=%%2F~%%2F\n"

# Check status
check_last_rc "Globus transfer submission failed" "$SUC_MSG\n$LINK"

# Save ID of new sync transfer
echo $GLOBUS_OUTPUT | tr -d '"' > "$LAST_TRANSFER_ID_FILE"

# rm -f $LOCKFILE
