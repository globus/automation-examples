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
  control to a user and, or, group. Uses a Native App grant or
  [Client Credential](http://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials/).
* `cleanup_cache.py`: removes directories under a shared endpoint that
  have had data transferred from them. Uses [Client Credential](http://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials/).


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

##### globus_folder_sync.py/cli-sync.sh

The app transfers `/share/godata/` directory from Tutorial Endpoint 1 to
`/~/sync-demo/` in a user's home directory on Tutorial Endpoint 2. To run the
app make sure that you have `sync-demo` directory created on Tutorial Endpoint
2, or change `DESTINATION_PATH` in `globus_folder_sync.py`. When you run the
app, the app will launch a web browser to get a authorization code. After you
consent, copy an authorization code to the app prompt:

```
$ python globus_folder_sync.py 
Native App Authorization URL: 
https://auth.globus.org/v2/oauth2/authorize?code_challenge=6xeOSl_5knYrzGPYZZRSme-rbA&state=_default&redirect_uri=https%3A%2F%2Fauth.globus.org%2Fv2%2Fweb%2Fauth-code&response_type=code&client_id=079bdf4e-9666-4816-ac01-7eab9dc82b93&scope=openid+email+profile+urn%3Aglobus%3Aauth%3Ascope%3Atransfer.api.globus.org%3Aall&code_challenge_method=S256&access_type=offline
Enter the auth code:
```

The shell script, cli-sync.sh, provides the same functionality. The script
stores a task id in last-transfer-id.txt to avoid multiple concurrent
transfers of the same files to the same destination:

```
$ bash cli-sync.sh 
$ cat last-transfer-id.txt
842ac3d8-39b5-11e7-bcec-22000b9a448b
```
##### share_data.py/share-data.sh

The app transfers `/share/godata/` directory from Tutorial Endpoint 1 to a
shared endpoint and destination path specified in the command line. Before
the app submits the transfer, it detects if a destination path already exists.
If it does and `--delete` option is specified, the app deletes the path, creates
it again and grant a specified user or group read access.
```
$ python share_data.py \
    --source-endpoint ddb59aef-6d04-11e5-ba46-22000b92c6ec \
    --shared-endpoint efc2bf94-35b7-11e7-bcd3-22000b9a448b \
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
The same functionality provides the shell script, share-data.sh. In this case,
a source endpoint and source path are hardcoded.
```
bash share-data.sh \
    --shared-endpoint efc2bf94-35b7-11e7-bcd3-22000b9a448b \
    --destination-path /share-data-demo/ \
    --user-uuid 94f0c387-9528-4bed-b373-4ad840f32661 \
    --delete
The directory was created successfully
Message: The transfer has been accepted and a task has been created and queued for execution
Task ID: 60b80d23-39c2-11e7-bcec-22000b9a448b
```
##### cleanup_cache.py
