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

# Destinatino Path
# The directory will be created if it doesn't exist
destination_path='/~/share-data/'

# User UUID transferred data will be shared with
user_id='johndoe@globusid.org'

# Group UUID transferred data will be shared with
group_uuid='94f0c387-9528-4bed-b373-4ad840f32661'


# Sync option
# Choices are
#   exists   TODO: add description
#   size     TODO: add description
#   mtime    TODO: add description
#   checksum TODO: add description
sync='checksum'

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

basename=`basename "$source_path"`
destination_directory="$destination_path$basename/"
globus ls "$shared_endpoint:$destination_directory" > /dev/null
if [ $? == 0 ]; then
    if [ -n "$delete" ]; then
        task_id=`globus delete --jq 'task_id' -r "$shared_endpoint:$destination_directory" | tr -d '"'`
        globus task wait $task_id
    else
        >&2 echo \
            'Destination directory already exists.' \
            'Delete the directory or use --delete option'
        exit 1
    fi
fi

globus mkdir "$shared_endpoint:$destination_directory"
rc=$?
check_rc

if [ x$user_id != x ]; then
    globus endpoint permission create --identity $user_id --permissions r "$shared_endpoint:$destination_directory"
fi
if [ x$group_uuid != x ]; then
    globus endpoint permission create --group $group_uuid --permissions r "$shared_endpoint:$destination_directory" 
fi

globus transfer --recursive --sync-level $sync "$source_endpoint:$source_path" "$shared_endpoint:$destination_directory"
