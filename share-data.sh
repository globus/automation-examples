#!/bin/bash

# This script transfers a folder to a shared endpoint
# and sets the sharing access control to a specified
# user, and, or group. The configuration options are
# defined below (source endpoint, shared endpoint, etc.).

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

# Sync options:
#   exists   Copy files that do not exist at the destination.
#   size     Copy files if the size of the destination does not match the size of the source.
#   mtime    Copy files if the timestamp of the destination is older than the timestamp of the source.
#   checksum Copy files if checksums of the source and destination do not match. Files on the destination are never deleted.
# For more information:
# $ globus transfer --help
# < OR >
# https://docs.globus.org/api/transfer/task_submit/#transfer_and_delete_documents
sync='checksum'

function help_and_exit () {

    echo -e 'Usage:' \
        "$0 --source-endpoint <UUID> --source-path <PATH> --shared-endpoint <UUID> --destination-path <PATH> [-d|--delete] [-h|--help]"
    echo ''
    echo 'The following options are available:'
    echo ''
    echo '  --source-endpoint: The endpoint you want to copy data from'
    echo '  --source-path: The path to the folder you want to copy to '
    echo '    your "--shared-endpoint"'
    echo '  --shared-endpoint: A shared endpoint you have created on'
    echo '    globus.org/app/transfer by clicking "share"'
    echo '  --destination-path: The path where "--source-path" folder'
    echo '    will be copied'
    echo '  --user-id: Email for user you want to grant access to your shared'
    echo '    endpoint'
    echo '  --group-uuid: Group UUID for a group you want to grant read access'
    echo '  --group-id: Alternative for "--group-uuid"'
    echo '  -d: Delete destination folder if it already exists'
    echo '  -h: Print this help message'
    echo ''
    echo "Example: $0 --source-endpoint ddb59aef-6d04-11e5-ba46-22000b92c6ec --source-path /share/godata --destination-path /shared_folder_example --shared-endpoint <your-shared-endpoint>"
    echo ''
    echo 'Go to "globus.org/app/transfer", navigate to your endpoint, and click'
    echo '"share" to create a shared endpoint'
    echo ''
    exit 0

}

if [ $# -eq 0 ]; then
    help_and_exit
fi


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
            help_and_exit
        ;;
        *)
            echo ''
            echo "Error: Unknown Option: '$1'"
            echo ''
            echo "$0 --help for options and more information."
            exit 1
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

# Add '/' if the user didn't provide one
if [ "${destination_path: -1}" != "/" ]; then
    destination_path="$destination_path/"
fi

destination_directory="$destination_path$basename/"
globus ls "$shared_endpoint:$destination_directory" 1>/dev/null 2>/dev/null
if [ $? == 0 ]; then
    # if it was, delete it
    if [ -n "$delete" ]; then
        echo "Destination directory, $destination_directory, exists and will be deleted"
        task_id=`globus delete --format unix --jmespath 'task_id' --label 'Share Data Example' -r "$shared_endpoint:$destination_directory"`
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

echo "Creating destination directory $destination_directory"
globus mkdir "$shared_endpoint:$destination_directory"
rc=$?
check_rc

if [ -n "$user_id" ]; then
    echo "Granting user, $user_id, read access to the destination directory"
    globus endpoint permission create --identity "$user_id" --permissions r "$shared_endpoint:$destination_directory"
fi
if [ -n "$group_uuid" ]; then
    echo "Granting group, $group_uuid, read access to the destination directory"
    globus endpoint permission create --group $group_uuid --permissions r "$shared_endpoint:$destination_directory"
fi

echo "Submitting a transfer from $source_endpoint:$source_path to $shared_endpoint:$destination_directory"
exec globus transfer --recursive --sync-level $sync --label 'Share Data Example' "$source_endpoint:$source_path" "$shared_endpoint:$destination_directory"
