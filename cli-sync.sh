#!/bin/bash

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

# Globus Tutorial Endpoint 1
source_endpoint='ddb59aef-6d04-11e5-ba46-22000b92c6ec'

# Globus Tutorial Endpoint 2
destination_endpoint='ddb59af0-6d04-11e5-ba46-22000b92c6ec'

# Sample data
source_path='/share/godata/'

# Destinatino Path
# The directory will be created if it doesn't exist
destination_path='/~/sync-demo/'

# Sync option
# Choices are
#   exists    TODO: add description
#   size     TODO: add description
#   mtime    TODO: add description
#   checksum TODO: add description
sync='checksum'

# TODO
# add ls to check that source is a directory

globus transfer --recursive --sync $sync "$source_endpoint:$source_path" "$destination_endpoint:$destination_path"
