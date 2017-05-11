#!/bin/bash

# Check if abort is necessary, and if so do it
function check_rc () {
    if [ $# -gt 0 ]; then
        abort_message="$1"
    fi

    if [ $rc -ne 0 ]; then
        exit 1
    fi
}

# Globus Tutorial Endpoint 1
source_endpoint='ddb59aef-6d04-11e5-ba46-22000b92c6ec'

# Globus Shared Endpoint
shared_endpoint=''

# Sample data
source_path='/share/godata/'

# Destination Path
destination_path='/'

# User UUID transferred data will be shared with
user_id='johndoe@globusid.org'

# Group UUID transferred data will be shared with
group_uuid=''


# Sync option
# Choices are
#   exists   TODO: add description
#   size     TODO: add description
#   mtime    TODO: add description
#   checksum TODO: add description
sync='checksum'

if [ -z $source_endpoint ]; then
    >&2 echo Error: Source endpoint is not defined
    exit 1
fi

if [ -z $shared_endpoint ]; then
    >&2 echo Error: Shared destination endpoint is not defined
    exit 1
fi

case "$destination_path" in
    /*)
        ;;
    *)
        >&2 echo Destination path must be absolute
        exit 1
        ;;
esac

case "$source_path" in
    /*)
    ;;
    *)
        >&2 echo Source path must be absolute
        exit 1
    ;;
esac

while [ $# -gt 0 ]; do
    key="$1"
    case $1 in
        -d|--delete)
            delete='yes'
        ;;
    esac
    shift
done

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
        task_id=`globus delete --jq 'task_id' -r "$shared_endpoint:$destination_directory" | tr -d '"'`
        globus task wait $task_id
    else
        >&2 echo \
            "Error: Destination directory, $destination_path$basename, already exists." \
            "Delete the directory or use --delete option"
        exit 1
    fi
else
    # if it was not, create a subdirectory
    globus mkdir "$shared_endpoint:$destination_directory"
    rc=$?
    check_rc
fi

if [ -n "$user_id" ]; then
    globus endpoint permission create --identity "$user_id" --permissions r "$shared_endpoint:$destination_directory"
fi
if [ -n "$group_uuid" ]; then
    globus endpoint permission create --group $group_uuid --permissions r "$shared_endpoint:$destination_directory"
fi

exec globus transfer --recursive --sync-level $sync "$source_endpoint:$source_path" "$shared_endpoint:$destination_directory"
