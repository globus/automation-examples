#!/bin/bash

# DESCRIPTION
#
# 1) Calls the Python gen_index.py script
# 2) Copies the index files from `tmp` (or other temporary folder) to `docs/examples/indexgen`
# 3) Does a `git add`, `git commit`, and `git push` on those (index) files

# Options for generating the index file(s):
#   directory           The directory in the shared endpoint where the data is located
#   local-index-dir     Specifies the name of the directory that is created when data is downloaded
#   no-json             Script will not create an index.json file
#   html-output         Generates an index.html file
#   markdown-output     Generates an index.md file
#   recursive           Generates (smaller) recursive index.html files instead of a single file
#   dest-endpoint       Index files will be uploaded to this endpoint instead of the shared endpoint
#   dest-path           Index files will be uploaded to this location/directory
#   include-filter      Filters the files and directories, all non-specified files/directories are excluded
#   exclude-filter      Filters the files and directories, excludes all specified files/directories
#   simple-parser       Downloads the (filtered) data from the shared endpoint, parses the data and generates a file containing the parsed data
#   case-insensitive    Makes the include/exclude filter(s) be case insensitive

while [ $# -gt 0 ]; do
    key="$1"
    case $1 in
        --local-endpoint)
            shift
            local_endpoint=$1
            args="--local-endpoint $local_endpoint"
        ;;
        --shared-endpoint)
            shift
            shared_endpoint=$1
            args="$args --shared-endpoint $shared_endpoint"
        ;;
        --directory)
            shift
            args="$args --directory $1"
        ;;
        --local-index-dir)
            shift
            local_index_dir=$1
            if [ "$local_index_dir" != "tmp"]
                then
                    args="$args --local-index-dir $local_index_dir"
            fi
        ;;
        --no-json)
            args="$args --no-json"
        ;;
        --html-output)
            html_output=true
            args="$args --html-output"
        ;;
        --markdown-output)
            args="$args --markdown-output"
        ;;
        --recursive)
            # no reason to use 'recursive' flag if html output is not enabled
            if [ ! -z "$html_output" ]
                then
                    args="$args --recursive"
            fi
        ;;
        --dest-endpoint)
            shift
            dest_endpoint=$1
        ;;
        --dest-path)
            if [ ! -z "$dest_endpoint" ]
                then
                    shift
                    args="$args --dest-endpoint $dest_endpoint --dest-path $1"
            fi
        ;;
        --include-filter)
            shift
            include_filter=$1
            args="$args --include-filter $include_filter"
        ;;
        --exclude-filter)
            shift
            exclude_filter=$1
            args="$args --exclude-filter $exclude_filter"
        ;;
        --simple-parser)
            args="$args --simple-parser"
        ;;
        --case-insensitive)
            # if there are no filters then there is no need to add the 'case-insensitive' flag
            if [ ! -z "$include_filter" ] || [ ! -z "$exclude_filter" ]
                then
                    args="$args --case-insensitive"
            fi
        ;;
        *)
            echo ''
            echo "Error: Unknown Option: '$1'"
            echo ''
            exit 1
    esac
    shift
done

# Check that local and shared endpoints are given
if [ -z $local_endpoint ]
    then
        echo 'Error: Local endpoint is not defined' >&2
        exit 1
fi
if [ -z $shared_endpoint ]
    then
        echo 'Error: Shared destination endpoint is not defined' >&2
        exit 1
fi

# Run the gen_index.py script with provided arguments (else statement may be unneccessary)
if [ ! -z "$args" ]
    then
        ./gen_index.py $args
    else
        echo "args failed: running basic script command (local and shared endpoint arguments only)"
        ./gen_index.py --local-endpoint $local_endpoint --shared-endpoint $shared_endpoint
fi

# copy all index.* files from tmp (or local_index_dir) to docs/examples/indexgen
cp tmp/index.* docs/examples/indexgen

# update the indexgen.html file in docs/examples/ for listing the index files generated (in gen_index.py script)
python docs/examples/gen_html.py   

# git add, commit, and push for the index files (in docs/examples/indexgen)
git add docs/examples/indexgen/*
git commit -m "updating index examples (from create-pages.sh)"
git push