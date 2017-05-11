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
* `sync.py`: submit a recursive transfer with sync option; uses a [Native
  App grant](https://github.com/globus/native-app-examples).
* `share-data.sh`: stages data to a folder and sets sharing access
  control to a user and, or, group.
* `cleanup_cache.py`: removes directories under a shared endpoint that
  have had data transferred from them. Uses a Native App grant.

## Getting Started
* Install the [Globus Command Line Interface (CLI)](https://docs.globus.org/cli/installation/).
* Set up your environment.
    * [OS X](#os-x)
    * [Linux](#linux-ubuntu)
    * [Windows](#windows)
* Create your own Native App registration for use with the examples. Visit the [Globus Developer Pages](https://developers.globus.org) to register an App.
    * When registering the App you'll be asked for some information, including the redirect URL and any scopes you will be requesting.
        * Check the "will be used by a native application checkbox"
        * Redirect URL: `https://auth.globus.org/v2/web/auth-code`
        * Scopes: `urn:globus:auth:scope:transfer.api.globus.org:all`, `openid`, `profile`, `email`

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
