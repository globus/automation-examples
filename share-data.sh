#!/bin/bash

# This script transfers a folder to a shared endpoint
# and sets the sharing access control to a specified
# user, and, or group. The configuration options are
# defined below (source endpoint, shared enpoint, etc.).

# Note that the shared endpoint UUID must be provided.

# Check if abort is necessary, and if so do it
function check_rc () {
    if [ $# -gt 0 ]; then
        abort_message="$1"
    fi

    if [ $rc -ne 0 ]; then
        exit 1
    fi
}

# Sync option
# Choices are
#   exists   TODO: add description
#   size     TODO: add description
#   mtime    TODO: add description
#   checksum TODO: add description
sync='checksum'


while [ $# -gt 0 ]; do
    key="$1"
    case $1 in
        --source-endpoint)
            shift
            source_endpoint=$1
        ;;
        --shared-endpoint)
            shift
            shared_endpoint=$1
        ;;
        --source-path)
            shift
            source_path=$1
        ;;
        --destination-path)
            shift
            destination_path=$1
        ;;
        --user-uuid|--user-id)
            shift
            user_id=$1
        ;;
        --group-uuid)
            shift
            group_uuid=$1
        ;;
        -d|--delete)
            delete='yes'
        ;;
        -h|--help)
            echo -e "Usage:" \
                "$0 --shared-endpoint <UUID> --destination-path <PATH> [-d|--delete] [-h|--help]"
            exit 0
        ;;
    esac
    shift
done

if [ -z $source_endpoint ]; then
    echo 'Error: Source endpoint is not defined' >&2
    exit 1
fi

if [ -z $shared_endpoint ]; then
    echo 'Error: Shared destination endpoint is not defined' >&2
    exit 1
fi

case "$destination_path" in
    /*)
        ;;
    *)
        echo 'Destination path must be absolute' >&2
        exit 1
        ;;
esac

case "$source_path" in
    /*)
    ;;
    *)
        echo 'Source path must be absolute' >&2
        exit 1
    ;;
esac

globus ls "$shared_endpoint:$destination_path" 1>/dev/null
rc=$?
check_rc

# check if a directory with the same name was already transferred to the destination path
basename=`basename "$source_path"`
destination_directory="$destination_path$basename/"
globus ls "$shared_endpoint:$destination_directory" 1>/dev/null 2>/dev/null
if [ $? == 0 ]; then
    # if it was, delete it
    if [ -n "$delete" ]; then
        task_id=`globus delete --jmespath 'task_id' -r "$shared_endpoint:$destination_directory" | tr -d '"'`
        globus task wait --timeout 600 $task_id
        rc=$?
        check_rc
    else
        >&2 echo \
            "Error: Destination directory, $destination_path$basename, already exists." \
            "Delete the directory or use --delete option"
        exit 1
    fi
fi
# create a destination subdirectory
globus mkdir "$shared_endpoint:$destination_directory"
rc=$?
check_rc

if [ -n "$user_id" ]; then
    globus endpoint permission create --identity "$user_id" --permissions r "$shared_endpoint:$destination_directory"
fi
if [ -n "$group_uuid" ]; then
    globus endpoint permission create --group $group_uuid --permissions r "$shared_endpoint:$destination_directory"
fi

exec globus transfer --recursive --sync-level $sync "$source_endpoint:$source_path" "$shared_endpoint:$destination_directory"
