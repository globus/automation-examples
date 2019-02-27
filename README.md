# Globus Automation Examples
Simple code examples for various use cases using Globus.

## Overview

There are three example use cases in this repo:

* Syncing a directory.
* Staging data in a shared directory.
* Removing directories after files are transferred .

The syncing and staging examples are implemented as both a Bash
script that calls the [Globus CLI](https://docs.globus.org/cli/) and 
a Python module that can be run as a script or imported as a module. 
The directory cleanup example is implemented as a Python script. 
The Python examples are built using the 
[Globus SDK](https://globus-sdk-python.readthedocs.io/en/stable/).

* [`cli-sync.sh`](cli-sync.sh): submit a recursive transfer with sync option.
* [`globus_folder_sync.py`](globus_folder_sync.py): submit a recursive transfer with sync option; uses a [Native App grant](https://github.com/globus/native-app-examples).
* [`share-data.sh`](share-data.sh): stages data to a folder and sets sharing access control to a user and or group.
* [`share_data.py`](share_data.py): stages data to a folder and sets sharing access control to a user and or group. Uses a [Native App grant](https://github.com/globus/native-app-examples) or [Client Credential grant](http://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials/).
* [`cleanup_cache.py`](cleanup_cache.py): removes directories under a shared endpoint that have had data transferred from them. Uses [Client Credential grant](http://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials/).

## Getting Started
* Install the [Globus Command Line Interface (CLI)](https://docs.globus.org/cli/installation/).
* Set up your environment.
    * [OS X](#os-x)
    * [Linux](#linux-ubuntu)
    * [Windows](#windows)
* Create your own Native App registration for use with the examples. Visit the [Globus Developer Pages](https://developers.globus.org) to register an App.
    * When registering the App you'll be asked for some information, including the redirect URL and any scopes you will be requesting.
        * Check the "Will be used by a native application" checkbox
        * Redirect URL: `https://auth.globus.org/v2/web/auth-code`
        * Scopes: `urn:globus:auth:scope:transfer.api.globus.org:all`, `openid`, `profile`, `email`
* Replace the UUIDs for `CLIENT_ID` in [`globus_folder_sync.py`](globus_folder_sync.py) and [`share_data.py`](share_data.py).
* If you prefer to run `share_data.py` as a Confidential App, visit the [Globus Developer Pages](https://developers.globus.org) to register an App.
    * Leave "Will be used by a native application" checkbox unchecked.
    * When your app is registerred, scroll down to "Client Secrets" and click "Generate New Client Secret". Copy a generated client secret into `share-data.py` as `CLIENT_SECRET`.

### OS X

##### Environment Setup

* `sudo easy_install pip`
* `sudo pip install virtualenv`
* `git clone https://github.com/globus/automation-examples`
* `cd automation-examples`
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements.txt`

### Linux (Ubuntu)

##### Environment Setup

* `sudo apt-get update`
* `sudo apt-get install python-pip`
* `sudo pip install virtualenv`
* `sudo apt-get install git`
* `git clone https://github.com/globus/automation-examples`
* `cd automation-examples`
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements.txt`

### Windows

##### Environment Setup

* Install Python (<https://www.python.org/downloads/windows/>)
* `pip install virtualenv`
* Install git (<https://git-scm.com/downloads>)
* `git clone https://github.com/globus/automation-examples`
* `cd automation-examples`
* `virtualenv venv`
* `venv\Scripts\activate`
* `pip install -r requirements.txt`

### Running the scripts

**Note**: Some of the examples will require you to login (see Login section for help).

##### globus_folder_sync.py and cli-sync.sh

The app transfers the `/share/godata/` directory from Tutorial Endpoint 1 to
`/~/sync-demo/` on Tutorial Endpoint 2. The destination path must exist
before the script is executed. The path can also be changed by specifying
a different value of `DESTINATION_PATH` in `globus_folder_sync.py`.
The Python script launches a web browser to get an OAuth authorization code.
After you consent and copy the code to the 'Enter the auth code' prompt,
the script requests access and refresh tokens from the Globus Auth service and
saves the tokens in the `transfer-data.json` file to avoid going through the OAuth
flow every time the script is executed.

```
$ ./globus_folder_sync.py 
Native App Authorization URL: 
https://auth.globus.org/v2/oauth2/authorize?code_challenge=6xeOSl_5knYrzGPYZZRSme-rbA&state=_default&redirect_uri=https%3A%2F%2Fauth.globus.org%2Fv2%2Fweb%2Fauth-code&response_type=code&client_id=079bdf4e-9666-4816-ac01-7eab9dc82b93&scope=openid+email+profile+urn%3Aglobus%3Aauth%3Ascope%3Atransfer.api.globus.org%3Aall&code_challenge_method=S256&access_type=offline
Enter the auth code:
Created directory: /~/sync-demo
Transfer has been started from
  ddb59aef-6d04-11e5-ba46-22000b92c6ec:/share/godata/
to
  ddb59af0-6d04-11e5-ba46-22000b92c6ec:/~/sync-demo
Visit the link below to see the changes:
https://globus.org/app/transfer?destination_path=%2F%7E%2Fsync-demo&origin_path=%2Fshare%2Fgodata%2F&destination_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec&origin_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
```
The same functionality can be implemented using the Globus CLI. In this case,
the Globus CLI is responsible for the OAuth 2.0 authorization flow and handling
access and refresh tokens. The example shell script, `cli-sync.sh`, calls
the Globus CLI `transfer` command only. To avoid transferring the same data
concurrently, the script stores a transfer task id in the `last-transfer-id.txt`
file and checks this file on every execution to avoid starting a new transfer before the previous task has finished.
```
$ globus login
$ ./cli-sync.sh 
Checking for a previous transfer
Last transfer fb55533e-449f-11e7-bd46-22000b9a448b SUCCEEDED, continuing
Verified that source is a directory
Submitted sync from ddb59aef-6d04-11e5-ba46-22000b92c6ec:/share/godata/ to ddb59af0-6d04-11e5-ba46-22000b92c6ec:/~/sync-demo/
Link:
https://www.globus.org/app/transfer?origin_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec&origin_path=%2Fshare%2Fgodata%2F&destination_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec&destination_path=%2F~%2Fsync-demo%2F
Saving sync transfer ID to last-transfer-id.txt
$ cat last-transfer-id.txt
842ac3d8-39b5-11e7-bcec-22000b9a448b
```

##### share_data.py and share-data.sh

The app transfers a directory to a shared endpoint and destination path
specified in the command line. The destination path must exist prior to running the script. Before the script starts transferring files it checks if the
destination path concatenated with the last section of the source path exists. If
it does and the `--delete` option is specified, the script deletes the path with
all subdirectories and files, creates it again and grants a specified user or
group read access.

**Note**: Before running this:
 * Create a shared endpoint and specify its UUID in the variable `$shared_ep`
 in the exmamples below.
 * Create a folder named `share-data-demo/` under the shared endpoint.

In the example below, the script transfers `/share/godata/` from Tutorial
Endpoint 1 to `/share-data-demo/` on a shared endpoint created against Tutorial
Endpoint 2. If you run this multiple times, you may see an error that the ACL rule
already exists. You can ignore it.
```
$ source_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec # Tutorial Endpoint 1
$ shared_ep='' # Shared endpoint on Tutorial Endpoint 2
$ user_uuid=c02d881a-d274-11e5-bdf5-d3a88fb071ca # John Doe
$ ./share_data.py \
    --source-endpoint $source_ep \
    --shared-endpoint $shared_ep \
    --source-path /share/godata/ \
    --destination-path /share-data-demo/ \
    --user-uuid $user_uuid \
    --delete
Native App Authorization URL: 
https://auth.globus.org/v2/oauth2/authorize?code_challenge=TUhBQXOSJhsSZSz9KVWzxwq7IhJCYXvuRaONlRK5BFc&state=_default&redirect_uri=https%3A%2F%2Fauth.globus.org%2Fv2%2Fweb%2Fauth-code&response_type=code&client_id=079bdf4e-9666-4816-ac01-7eab9dc82b93&scope=openid+email+profile+urn%3Aglobus%3Aauth%3Ascope%3Atransfer.api.globus.org%3Aall&code_challenge_method=S256&access_type=offline
Enter the auth code: 
Creating destination directory /share-data-demo/godata/
Granting user, c02d881a-d274-11e5-bdf5-d3a88fb071ca, read access to the destination directory
Submitting a transfer task
	task_id: db404718-44a2-11e7-bd46-22000b9a448b
You can monitor the transfer task programmatically using Globus SDK, or go to the Web UI, https://www.globus.org/app/activity/db404718-44a2-11e7-bd46-22000b9a448b.    
```
`share-data.sh` script shows how to implement the same functionality using the Globus CLI.
```
$ globus login
$ source_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec # Tutorial Endpoint 1
$ shared_ep='' # Shared endpoint on Tutorial Endpoint 2
$ user_uuid=c02d881a-d274-11e5-bdf5-d3a88fb071ca # John Doe
$ ./share-data.sh \
    --source-endpoint $source_ep \
    --shared-endpoint $shared_ep \
    --source-path /share/godata/ \
    --destination-path /share-data-demo/ \
    --user-uuid $user_uuid \
    --delete
Destination directory, /share-data-demo/godata/, exists and will be deleted
The directory was created successfully
Message: The transfer has been accepted and a task has been created and queued for execution
Task ID: 60b80d23-39c2-11e7-bcec-22000b9a448b
```

##### gen_index.py

The default behavior of this script is to create a single JSON file that lists all the files, and their attributes, in a given endpoint and path (subdirectories included). The following optional flags can change what kind of output (index) files you get:
* `--no-json`: this flag stops the script from generating the JSON file
* `--html-output`: this flag tells the script to generate an index.html file for the given endpoint and path
* `--markdown-output`: this flag tells the script to generate an index.md file for the given endpoint and path

A list containing all of the arguments and their descriptions can be obtained by entering `python gen_index.py -h` in the command line.

**Note**: It is assummed that the shared endpoint used in the examples below is the same one from the examples for the share_data.py and share-data.sh scripts. You will also need to set up your own (local) Globus Connect Personal Endpoint (for help see the `How To` found at https://docs.globus.org/how-to/ for your machine)

The examples below demonstrates a few of the possible behaviors of the script.

```
# All of the examples for this script will use the following:
$ local_ep='' # UUID of your local Globus Connect Personal Endpoint
$ shared_ep='' # Shared endpoint (UUID) on Tutorial Endpoint 2
```
The example below shows the most basic use for this script.
```
$ ./gen_index.py \ 
    --local-endpoint $local_ep \
    --shared-endpoint $shared_ep
```
The example below is similar to the basic case (example above), but also enables HTML and Markdown index files using the `--html-output` and `--markdown-output` flags respectively.
```
$ ./gen_index.py \
    --local-endpoint $local_ep \
    --shared-endpont $shared_ep \
    --html-output \
    --markdown-output
```
The example below disables JSON output by using the `--no-json` flag and enables HTML and Markdown index files using the `--html-output` and `--markdown-output` flags respectively.
```
$ ./gen_index.py \
    --local-endpoint $local_ep \
    --shared-endpont $shared_ep \
    --no-json \
    --html-output \
    --markdown-output
```
###### Using Filters
The script also supports `include` and `exclude` filters. Include filters allow you to specify files and directories to include in the list, and stop the script from adding any files or directories not specified in the filters (see the example below).
```
# This example tells the script to only list the files and directories in the `sync-demo` and `share-data-demo` folders
$ include_filters = 'sync-demo share-data-demo'
$ ./gen_index.py \
    --local-endoint $local_ep \
    --shared-endpoint $shared_ep \
    --include-filter $include_filters
```
Similarly, `exclude` filters allow you to specify files and directories that you do not want included in the list (see the example below).
```
# This example tells the script to ignore all files named `file1.txt` and any directories called `godata` (and the respective sub-folders and files)
$ exclude_filters = 'file1.txt godata'
$ ./gen_index.py \
    --local-endoint $local_ep \
    --shared-endpoint $shared_ep \
    --exclude-filter $exclude_filters
```
It is also possible to use both types of filters at the same time (see the example below). In these cases, include filters will always be applied prior to exclude filters.
```
# This example tells the script to only list files and directories in the `sync-demo` and `share-data-demo` folders, except for any directories called `godata` and files called `file1.txt`
$ include_filters = 'sync-demo share-data-demo'
$ exclude_filters = 'file1.txt godata'
$ ./gen_index.py \
    --local-endpoint $local_ep \
    --shared-endpoint $shared_ep \
    --include-filter $include_filters \
    --exclude-filter $exclude_filters
```
###### Parsing Files

##### cleanup_cache.py

There are a few things that are necessary to set up in order to successfully run [`cleanup_cache.py`](cleanup_cache.py).

* You must have registered a ClientID and generated a secret for it at [Globus Developer Pages](https://developers.globus.org).  Since this script uses a Client Credential Grant, embedding the client secret in the script, you should not use this ClientID for any other purposes. When creating the app use the following:
    * "Redirect URLs" -- Set to `https://example.com/oauth_callback/`.
    * Scopes: `[urn:globus:auth:scope:transfer.api.globus.org:all]`
        Only transfer is required, since your bot will be using client_secret
        to authenticate. `[openid profile]` are required if you setup your own
        three-legged-auth server and want to allow users to login to it.
    * Leave "Native App" unchecked.
* The ClientID and secret that you obtained above should be placed in the `cleanup_cache.py` script, in place of the development values.
* There must be a shared endpoint, the transfers from which you wish to monitor and clean up.
* The Client Identity Username (typically the Client ID with "@clients.auth.globus.org appended) must be authorized as an Administrator and Activity Monitor of your shared endpoint. You can set these at `https://www.globus.org/app/endpoints/<UUID of shared endpoint>/roles`.
* You must put the UUID of the shared endpoint you wish to clean up in the `cleanup_cache.py` script.

The `cleanup_cache.py` script will do the following:

* Search for successful transfers from your shared endpoint within the last 24 hours.
* For any successful transfers found, determine if the files transferred were in a common directory, if so, submit a recursive delete request on that directory, if not, submit a delete request for each file from the transfer.
* Determine if the common directory from the transfer had any specific ACLs set on the endpoint, if so, delete them.

Note: `cleanup_cache.py` will find the most specific common directory for all files copied in a transfer.  Thus, if all the files transferred were in `/maindir/subdir`, it will attempt to recursively delete `/maindir/subdir`, not `/maindir`.

Another Note: This script is greedy in how it deletes folders. If someone cherry-picks files, it will still delete the whole directory!

### Login

Some of the scripts require you to login to Globus to ensure that you are an authorized user. The scripts use refresh tokens to save you the trouble of needing to login every time a script is run. For example, if you login when running a script and then run either the same script or a different one, you will not need to login a second time. 
