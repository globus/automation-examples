# Developer Tutorial Examples
Simple code examples for various use cases using Globus.

## Overview

There are three example use cases in this repo:

* Syncing a directory
* Staging data in a shared directory
* Removing directories after files are transferred 

The syncing and staging examples are implemented as both a Bash
script that calls the [Globus CLI](https://docs.globus.org/cli/) and 
a Python module that can be run as a script or imported as a module. 
The directory cleanup example is only implemented as a Python script. 
The Python examples modules are built on the 
[Globus SDK](https://globus-sdk-python.readthedocs.io/en/stable/).

* `cli-sync.sh`: submit a recursive transfer with sync option.
* `globus_folder_sync.py`: submit a recursive transfer with sync option; uses a [Native
  App grant](https://github.com/globus/native-app-examples).
* `share-data.sh`: stages data to a folder and sets sharing access
  control to a user and, or, group.
* `share_data.py`: stages data to a folder and sets sharing access
  control to a user and, or, group. Uses a [Native
  App grant](https://github.com/globus/native-app-examples) or
  [Client Credential grant](http://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials/).
* `cleanup_cache.py`: removes directories under a shared endpoint that
  have had data transferred from them. Uses [Client Credential grant](http://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials/).


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
* If you prefer to run share-data.py as a Confidential App, visit the [Globus Developer Pages](https://developers.globus.org) to register an App.
    * Leave "Will be used by a native application" checkbox unchecked
    * When your app is registerred, scroll down to 'Client Secrets' and click 'Generate New Client Secret'. Copy a generated client secret to share-data.py as CLIENT_SECRET.

### OS X

##### Environment Setup

* `sudo easy_install pip`
* `sudo pip install virtualenv`
* `git clone https://github.com/globus/native-app-examples`
* `cd native-app-examples`
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements.txt`

### Linux (Ubuntu)

##### Environment Setup

* `sudo apt-get update`
* `sudo apt-get install python-pip`
* `sudo pip install virtualenv`
* `sudo apt-get install git`
* `git clone https://github.com/globus/native-app-examples`
* `cd native-app-examples`
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements.txt`

### Windows

##### Environment Setup

* Install Python (<https://www.python.org/downloads/windows/>)
* `pip install virtualenv`
* Install git (<https://git-scm.com/downloads>)
* `git clone https://github.com/globus/native-app-examples`
* `cd native-app-examples`
* `virtualenv venv`
* `venv\Scripts\activate`
* `pip install -r requirements.txt`

### Running the scripts

##### globus_folder_sync.py and cli-sync.sh

The app transfers `/share/godata/` directory from Tutorial Endpoint 1 to
`/~/sync-demo/` on Tutorial Endpoint 2. The destination path must exist
before the script is executed. The path can also be changed by specifying
a different value of `DESTINATION_PATH` in `globus_folder_sync.py`.
The script launches a web browser to get an OAuth authorization code.
After you consent and copy the code to the 'Enter the auth code' prompt,
the script requests access and refresh tokens from the Globus Auth service and
saves the tokens in transfer-data.json file to avoid going through the OAuth
flow every time, when the application is executed.

```
$ python globus_folder_sync.py 
Native App Authorization URL: 
https://auth.globus.org/v2/oauth2/authorize?code_challenge=6xeOSl_5knYrzGPYZZRSme-rbA&state=_default&redirect_uri=https%3A%2F%2Fauth.globus.org%2Fv2%2Fweb%2Fauth-code&response_type=code&client_id=079bdf4e-9666-4816-ac01-7eab9dc82b93&scope=openid+email+profile+urn%3Aglobus%3Aauth%3Ascope%3Atransfer.api.globus.org%3Aall&code_challenge_method=S256&access_type=offline
Enter the auth code:
```
The same functionality can be implemented using Globus CLI. In this case,
Globus CLI is responsible for the OAuth 2.0 authorization flow and handling
access and refresh tokens. The example shell script, cli-sync.sh, calls
the Globus CLI transfer command only. To avoid transferring the same data
concurrently, the script stores a transfer task id in last-transfer-id.txt
file and checks this file on every execution to avoid the same files are
transferred concurrently.
```
$ globus login
$ bash cli-sync.sh 
$ cat last-transfer-id.txt
842ac3d8-39b5-11e7-bcec-22000b9a448b
```
##### share_data.py and share-data.sh

The app transfers a directory to a shared endpoint and destination path
specified in the command line. You have to make sure the destination path
exists. Before the script starts transferring files, it checks if the
destination path concatenated with the last bit of the source path exists. If
it does and `--delete` option is specified, the script deletes the path with
all subdirectories and files, creates it again and grant a specified user or
group read access.
In the example below, the script transfers `/share/godata/` from Tutorial
Endpoint 1 to `/share-data-demo/` on a shared endpoint made of Tutorial
Endpoint 2.
```
$ python share_data.py \
    --source-endpoint ddb59aef-6d04-11e5-ba46-22000b92c6ec \ # Tutorial Endpoint 1
    --shared-endpoint fc1fde1e-3a41-11e7-bcf2-22000b9a448b \ # Shared endpoint on Tutorial Endpoint 2
    --source-path /share/godata/ \
    --destination-path /share-data-demo/ \
    --user-uuid 94f0c387-9528-4bed-b373-4ad840f32661 \
    --delete
Destination directory, /share-data-demo/godata/, exists and will be deleted
Submitting a delete task
    task_id: f5a8747e-39ba-11e7-bcec-22000b9a448b
Creating destination directory /share-data-demo/godata/
Granting user, 94f0c387-9528-4bed-b373-4ad840f32661, read access to the destination directory
Submitting a transfer task
    task_id: fc4b38b6-39ba-11e7-bcec-22000b9a448b
You can monitor the transfer task programmatically using Globus SDK, or, if you run it as a native app,
go to the Web UI, https://www.globus.org/app/activity/fc4b38b6-39ba-11e7-bcec-22000b9a448b.
```
Share-data.sh script shows how to implement the same functionality using Globus CLI.
```
$ globus login
$ bash share-data.sh \
    --source-endpoint ddb59aef-6d04-11e5-ba46-22000b92c6ec \ # Tutorial Endpoint 1
    --shared-endpoint fc1fde1e-3a41-11e7-bcf2-22000b9a448b \ # Shared endpoint on Tutorial Endpoint 2
    --source-path /share/godata/ \
    --destination-path /share-data-demo/ \
    --user-uuid 94f0c387-9528-4bed-b373-4ad840f32661 \
    --delete
The directory was created successfully
Message: The transfer has been accepted and a task has been created and queued for execution
Task ID: 60b80d23-39c2-11e7-bcec-22000b9a448b
```
##### cleanup_cache.py
