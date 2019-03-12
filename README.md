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
Transfer has been started from
  ddb59aef-6d04-11e5-ba46-22000b92c6ec:/share/godata/
to
  ddb59af0-6d04-11e5-ba46-22000b92c6ec:/~/sync-demo/
Visit the link below to see the changes:
https://globus.org/app/transfer?destination_path=%2F%7E%2Fsync-demo%2F&origin_path=%2Fshare%2Fgodata%2F&destination_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec&origin_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
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
Destination directory, /share-data-demo/godata/, exists and will be deleted
Submitting a delete task
	task_id: 3d68afa2-3943-11e9-9fa6-0a06afd4a22e
Creating destination directory /share-data-demo/godata/
Granting user, 78af45b1-d0b4-4311-8475-b3681d37c4d5, read access to the destination directory
Submitting a transfer task
	task_id: 4409c314-3943-11e9-9fa6-0a06afd4a22e
You can monitor the transfer task programmatically using Globus SDK, or go to the Web UI, https://www.globus.org/app/activity/4409c314-3943-11e9-9fa6-0a06afd4a22e.    
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

**Note**: Both share_data.py and share-data.sh require you to login (see Login section for help).

##### gen_index.py

The default behavior of this script is to create a single JSON file that lists all the files, and their attributes, in a given endpoint and path (subdirectories included). The following optional flags can change what kind of output (index) files you get:
* `--no-json`: this flag stops the script from generating the JSON file
* `--html-output`: this flag tells the script to generate an index.html file for the given endpoint and path
* `--markdown-output`: this flag tells the script to generate an index.md file for the given endpoint and path

A list containing all of the arguments and their descriptions can be obtained by entering `python gen_index.py -h` in the command line. The order that the arguments are given will not affect the behavior of the script.

**Note**: It is assummed that the shared endpoint used in the examples below is the same one from the examples for the share_data.py and share-data.sh scripts. You will also need to set up your own (local) Globus Connect Personal Endpoint (for help see the `How To` found at https://docs.globus.org/how-to/ for your machine). It is also important to ensure that you have the correct permissions for both the shared and local endpoints. 

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

###### Default Behavior
In addition to the previously mentioned options, there are certain actions that the script takes by default that can be changed if certain arguments are provided.
* **Destination Endpoint and Directory**
    * By default, the script uploads the index files to the provided shared endpoint and it's root (`/`) directory. It is possible to change this behavior by using the `--dest-endpoint` and `--dest-path` arguments to change the upload endpoint and directory respectively. This will only work if BOTH arguments are given; if only one is provided then the script will resort to it's default behavior.

* **Recursive Index Files (only applies to HTML)**
    * By default, the script generates a single `index.html` file that lists all of the files and directories, but it is possible to change this behavior by ussing the `--recursive` flag. This flag tells the script to create multiple (smaller) `index.html` files instead of a single large one. This means that every directory (starting from the root, or `tmp`, directory) will have an `index.html` file that lists the contents of that directory (see below for examples).
    * This option only applies to the HTML index file(s); enabling this option without the `--html-output` flag will NOT change the script's default behavior.

Example Directory (before the script):
* FolderA
    * File1.txt
    * Folder2
        * FileA.txt
* FolderB

Example Directory (after the script, assume that FolderA and FolderB are in the `tmp` folder):
* FolderA
    * File1.txt
    * index.html
    * Folder2
        * FileA.txt
        * index.html
* FolderB
    * index.html
* index.html

###### Using Filters

The script also supports `include` and `exclude` filters. Include filters allow you to specify files and directories to include in the list, and stop the script from adding any files or directories not specified in the filters (see the example below).

**Note:** When the script checks file and directory names against the filter(s), it is checking for an exact match. This means that if you have a "file1.txt" that you want to exclude, but you pass the argument as "file.txt" then the "file1.txt" will not be excluded. Also, the filters are case-sensitive by default, but this can be changed by using the `--case-insensitive` flag.
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
# This example tells the script to ignore all files named "file1.txt" and any directories called "godata" (and the respective sub-folders and files). If the '--case-insensitive' flag were not provided then the script would not ignore the previously mentioned files and directories, since the case(s) would not match.
$ exclude_filters = 'File1.tXt goData'
$ ./gen_index.py \
    --local-endoint $local_ep \
    --shared-endpoint $shared_ep \
    --exclude-filter $exclude_filters
    --case-insensitive
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

If you want to filter files or directories that match a certain pattern then you should use Unix shell-style wildcards.

**Note:** If you use wildcards, you will need to provide the filters in-line rather than storing them in a variable, otherwise they will be interpreted differently (e.g., '*.txt' becomes 'requirements.txt').
```
# This example tells the script to exclude all files and directories that end in ".txt", and include all files and directories that contain the word "data"
$ ./gen_index.py \
    --local-endpoint $local_ep \
    --shared-endpoint $shared_ep \
    --exclude-filter '*.txt' \
    --include-filter '*data*'
```

###### Parsing Files
The script also supports the option to parse the files in order to extract more information. Using the `--simple-parser` flag will enable this option and cause the script to parse the files and write the resulting metadata to a `parsed-data.json` file that will be saved to the provided local endpoint. Part of this process will involve downloading all of the files and folders from the shared endpoint to the local endpoint (and their respective directories), which will be stored in a temporary (`tmp`) folder.

For details on how the Tika Python parser works, see: https://github.com/chrismattmann/tika-python 

**Note**: It is assummed that the `tmp` folder and `parsed-data.json` file do not exist prior to running the script. To avoid errors or overwriting existing data it is recommended to either delete or rename any existing file or folder with those names. You can also go into the code and change the `local_index_dir` variable if you want the created folder to have a different name. In addition, it is possible to use the `include` and `exclude` filters with the parser; the command for this option is the same as in the Filter examples, just add the `--simple-parser` flag.

The following is an example of the parser's basic behavior.
```
# This example generates the HTML and JSON index files, downloads the files from the shared endpont to the local endpoint, and generates a parsed-data.json file that contains the downloaded files metadata.
$ ./gen_index.py \
    --local-endpoint $local_ep \
    --shared-endpoint $shared_ep \
    --html-output \
    --simple-parser
/godata
/share-data-demo
/share-data-demo/godata
/share-data-demo/shared_dir
/sync-demo
Creating a transfer task with all index.html and index.md files...
3300136e-2a27-11e9-9351-0e3d676669f4:/Users/[username]/automation-examples/tmp/index.html -> 152ea4ac-28c6-11e9-9836-0262a1f2f698:/index.html
Submitting a transfer task...
	task_id: 7ccb41fc-3b80-11e9-9e65-0266b1fe9f9e
You can monitor the transfer task programmatically using Globus SDK, or go to the Web UI, https://www.globus.org/app/activity/7ccb41fc-3b80-11e9-9e65-0266b1fe9f9e.

Getting the files and directories to parse:
Failed to create directory at path: /Users/[username]/automation-examples/tmp/share-data-demo/godata

Submitting a transfer task...
	task_id: 7d16cc58-3b80-11e9-9e65-0266b1fe9f9e
You can monitor the transfer task programmatically using Globus SDK, or go to the Web UI, https://www.globus.org/app/activity/7d16cc58-3b80-11e9-9e65-0266b1fe9f9e.

Starting the Simple Parser:
Generating "parsed_results.json" file in: /Users/[username]/automation-examples
```
Some things to note from the example above:
* Getting a "Failed to create directory at path..." message
    * The purpose of this message is to inform you that the script was unable to create the specified directory (at the given location). The most common cause of this message is that the directory in question already exists.
    * It is possible to get multiple instances of this message (e.g., if more than one of the directories already exist).
    * If you see this message then it is recommended that you check to make sure that the directory in question was successfully downloaded and accurately reflects the contents of the shared endpoint and directory that it was downloaded from.
* /Users/[username]/automation-examples
    * This path represents the main (local) directory that you are running the script from and may be different for you.
         * [username] is just a placeholder and will differ depending on the individual.
         
##### create-pages.sh
This script calls the gen_index.py script, copies the index files generated from the `tmp` directory to the `docs/examples/indexgen/` directory, and commits and pushes those files to the GitHub repository. The purpose of the script is to automate the process of updating the GitHub Page for the repository.

Things to keep in mind:
* The GitHub repository that the files will be committed and pushed to is whichever one you are currently on.
    * In most cases, this should be the `globus/automation-examples` repository.
    * If you have forked the `globus/automation-examples` or are using a different repository, make sure that that GitHub Pages is set up correctly for your repository (see steps below)
        * Step 1) Go to your GitHub repository
        * Step 2) Navigate to the `GitHub Pages Settings (Settings -> GitHub Pages)`
        * Step 3) For `Source` choose `master branch /docs folder`
    * Make sure that you are in the `master` branch, as GitHub Pages does not look at any of the other branches.
* The arguments that the script takes are the same as the arguments for running the `gen_index.py` script (see below for an example)
* The script assumes that the `docs`, `docs/examples`, and `docs/examples/indexgen` directories already exist (in the root directory).
```
$ local_ep='' # UUID of your local Globus Connect Personal Endpoint
$ shared_ep='' # Shared endpoint (UUID) on Tutorial Endpoint 2
$ ./create-pages.sh \
    --local-endpoint $local_ep \
    --shared-endpoint $shared_ep \
    --simple-parser \
    --markdown-output
/godata
/share-data-demo
/share-data-demo/godata
/share-data-demo/shared_dir
/sync-demo
Creating a transfer task with all index.html and index.md files...
3300136e-2a27-11e9-9351-0e3d676669f4:/Users/[username]/automation-examples/tmp/index.md -> 152ea4ac-28c6-11e9-9836-0262a1f2f698:/index.md
Submitting a transfer task...
	task_id: 2c10f088-3f84-11e9-9e69-0266b1fe9f9e
You can monitor the transfer task programmatically using Globus SDK, or go to the Web UI, https://www.globus.org/app/activity/2c10f088-3f84-11e9-9e69-0266b1fe9f9e.

Getting the files and directories to parse:
Failed to create directory at path: /Users/[username]/automation-examples/tmp/share-data-demo/godata

Submitting a transfer task...
	task_id: 2c6424a6-3f84-11e9-9e69-0266b1fe9f9e
You can monitor the transfer task programmatically using Globus SDK, or go to the Web UI, https://www.globus.org/app/activity/2c6424a6-3f84-11e9-9e69-0266b1fe9f9e.

Starting the Simple Parser:
Generating "parsed_results.json" file in: /Users/[username]/automation-examples
[master cd86fbd] updating index examples (from create-pages.sh)
 2 files changed, 257 insertions(+)
 create mode 100644 docs/examples/indexgen/index.json
 create mode 100644 docs/examples/indexgen/index.md
Counting objects: 7, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (7/7), done.
Writing objects: 100% (7/7), 1.48 KiB | 1.48 MiB/s, done.
Total 7 (delta 1), reused 0 (delta 0)
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To https://github.com/globus/automation-examples.git
   b1d293a..cd86fbd  master -> master
```

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
