#!/bin/sh

# DESCRIPTION
#
# 1) Calls the Python gen_index.py script
# 2) Copies the index files from `tmp` to `docs/examples/indexgen`
# 3) Does a `git add`, `git commit`, and `git push` on those (index) files

# gen_index_dir located in Globus Tutorial Endpoint 1
SHARED_ENDPOINT='e1e88d04-3c63-11e9-a613-0a54e005f950'

# Request destination (e.g., local) endpoint UUID
echo "Please enter the UUID for the destination endpoint:"
read destination_ep

function