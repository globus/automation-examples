# Developer Tutorial Examples
Simple code examples for various use cases using Globus [Auth](https://docs.globus.org/api/auth/).

## Overview
All examples use the Globus Python SDK and the Native App Authorization Flow.
* `example_copy_paste.py` -- get an access token for Transfer and do an `ls` on an endpoint.
* `example_copy_paste_refresh_token.py` -- get a refresh token for Transfer and do an `ls` on an endpoint and automatically retrieve a new access token when necessary.
* `example_local_server.py` -- demonstrate how an app could use a local web server to automatically receive the "auth code."

## Getting Started
* Set up your environment.
    * [OS X](#os-x)
    * [Linux](#linux-ubuntu)
    * [Windows](#windows)
* Create your own Native App registration for use with the examples. Visit the [Globus Developer Pages](https://developers.globus.org) to register an App.
    * When registering the App you'll be asked for some information, including the redirect URL and any scopes you will be requesting.
        * Check the "will be used by a native application checkbox"
        * Redirect URL: `https://auth.globus.org/v2/web/auth-code` and `http://localhost:8000`
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
