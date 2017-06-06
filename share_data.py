#!/usr/bin/env python

"""
Copy data from your private endpoint to a shared one for other people
to access. You can share data with both individual users and groups.

Required: You create a shared endpoint by going to globus.org/app/transfer
navigating to an Endpoint, and clicking "share". You can use "Globus Tutorial
Endpoint 2" for testing.

Choose a data source. You can use "Globus Tutorial Endpoint 1" for testing.

Register your own app at developers.globus.org. Configure as follows:
Native App:
    * "Redirect URLs" -- Set to "https://auth.globus.org/v2/web/auth-code".
        You can setup your own server for distributing auth codes if you wish.
    * Scopes:
        [openid profile urn:globus:auth:scope:transfer.api.globus.org:all]
        openid and profile are required for auth, transfer.api.globus.org
        for transfers.
    * Check "Native App".
Confidential App [Client Credentials Grant]:
    * "Redirect URLs" -- Set to "https://auth.globus.org/v2/web/auth-code".
        Confidential apps also allow you to setup your own server for three-
        legged-auth with auth.globus.org if you wish. You may therefore put
        https://example.com/oauth_callback/ instead.
    * Scopes:
        [urn:globus:auth:scope:transfer.api.globus.org:all]
        Only transfer is required, since your bot will be using client_secret
        to authenticate. [openid profile] are required if you setup your own
        three-legged-auth server and want to allow users to login to it.
    * Uncheck "Native App".

Tutorial Endpoint IDs
Globus Tutorial Endpoint 1: ddb59aef-6d04-11e5-ba46-22000b92c6ec
Globus Tutorial Endpoint 2: ddb59af0-6d04-11e5-ba46-22000b92c6ec
"""

from __future__ import print_function
import os
import sys
import argparse
import webbrowser
import json
import globus_sdk
from globus_sdk.exc import TransferAPIError

# Both Native App and Client Credential authentication require Client IDs.
# Create your app at developers.globus.org. The following id is for testing
# only and should not be relied upon (You should create your own app).
CLIENT_ID = '079bdf4e-9666-4816-ac01-7eab9dc82b93'

# Client Secret is only needed for Confidential apps. Make your app
# confidential instead of native by _not_ checking the 'Native App' checkbox
# on developers.globus.org for your app.
CLIENT_SECRET = ''

# Native is better for user machines, where the user is capable of hitting
# a browser to get an authentication code. Native only stores temporary
# access tokens (unless you enable refresh tokens), and does not require
# safeguarding client secrets.
#
# Client Credentials grant requires storing a 'client_secret', which does
# not require a browser or user intervention, but does require safeguarding
# the client_secret. Use Confidential on servers or trusted machines.
# *Notice*: A confidential app is a bot which acts on your behalf. You will
# need to give it permission to access your shared endpoint. You can do so
# with globus-cli via:
# globus endpoint permission create
#   --identity <client_id>@clients.auth.globus.org
#   <Your shared_endpoint UUID>:/
#   --permissions rw
# (Your bot's identity will always match the client id for your
# app + '@clients.auth.globus.org')
#
# You can also go to globus.org/app/endpoints?scope=shared-by-me and under
# "Identity/E-mail" set: "<client_id>@clients.auth.globus.org"
APP_AUTHENTICATORS = ('native', 'client-credentials')

# Default is native for this script.
AUTHENTICATION = 'native'

# Redirect URI specified when registering a native app
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'

# For this example, we will be liberal with scopes.
SCOPES = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')

TOKEN_FILE = 'refresh-tokens.json'

# Example: Globus Tutorial Endpoint 1
source_endpoint = 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'

# Choose which shared folder you want to use.
# Example: Go to globus.org/app/transfer and select:
#     Endpoint: Globus Tutorial Endpoint 2
#     Path: /~/
#     And click 'share' to create your home directory as the shared endpoint.
shared_endpoint = ''

# Source data. The example below is three files on Globus Tutorial Endpoint 1
source_path = '/share/godata'

# Destination on the shared endpoint. Note that this example copies files
# to the 'root' of the _shared_ endpoint, which in the example above we
# selected as '/~/'. The final result of this example will be three files
# stored on Globus Tutorial Endpoint 2 at /~/godata/.
destination_path = '/'

get_input = getattr(__builtins__, 'raw_input', input)


def load_tokens_from_file(filepath):
    """Load a set of saved tokens."""
    with open(filepath, 'r') as f:
        tokens = json.load(f)

    return tokens


def save_tokens_to_file(filepath, tokens):
    """Save a set of tokens for later use."""
    with open(filepath, 'w') as f:
        json.dump(tokens, f)


def update_tokens_file_on_refresh(token_response):
    """
    Callback function passed into the RefreshTokenAuthorizer.
    Will be invoked any time a new access token is fetched.
    """
    save_tokens_to_file(TOKEN_FILE, token_response.by_resource_server)


def is_remote_session():
    """
    Check if this is a remote session, in which case we can't open a browser
    on the users computer. This is required for Native App Authentication (but
    not a Client Credentials Grant).
    Returns True on remote session, False otherwise.
    """
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


def eprint(*args, **kwargs):
    """Same as print, but to standard error"""
    print(*args, file=sys.stderr, **kwargs)


def do_native_app_authentication(client_id, redirect_uri,
                                 requested_scopes=None):
    """
    Does a Native App authentication flow and returns a
    dict of tokens keyed by service name.
    """
    client = globus_sdk.NativeAppAuthClient(client_id=client_id)
    # pass refresh_tokens=True to request refresh tokens
    client.oauth2_start_flow(
            requested_scopes=requested_scopes,
            redirect_uri=redirect_uri,
            refresh_tokens=True)

    url = client.oauth2_get_authorize_url()

    print('Native App Authorization URL: \n{}'.format(url))

    if not is_remote_session():
        # There was a bug in webbrowser recently that this fixes:
        # https://bugs.python.org/issue30392
        if sys.platform == 'darwin':
            webbrowser.get('safari').open(url, new=1)
        else:
            webbrowser.open(url, new=1)

    auth_code = get_input('Enter the auth code: ').strip()

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # return a set of tokens, organized by resource server name
    return token_response.by_resource_server


def get_native_app_authorizer(client_id):
    tokens = None
    try:
        # if we already have tokens, load and use them
        tokens = load_tokens_from_file(TOKEN_FILE)
    except:
        pass

    if not tokens:
        tokens = do_native_app_authentication(
                client_id=client_id,
                redirect_uri=REDIRECT_URI,
                requested_scopes=SCOPES)
        try:
            save_tokens_to_file(TOKEN_FILE, tokens)
        except:
            pass

    transfer_tokens = tokens['transfer.api.globus.org']

    auth_client = globus_sdk.NativeAppAuthClient(client_id=client_id)

    return globus_sdk.RefreshTokenAuthorizer(
            transfer_tokens['refresh_token'],
            auth_client,
            access_token=transfer_tokens['access_token'],
            expires_at=transfer_tokens['expires_at_seconds'],
            on_refresh=update_tokens_file_on_refresh)


def do_client_credentials_app_authentication(client_id, client_secret):
    """
    Does a client credential grant authentication and returns a
    dict of tokens keyed by service name.
    """
    client = globus_sdk.ConfidentialAppAuthClient(
            client_id=client_id,
            client_secret=client_secret)
    token_response = client.oauth2_client_credentials_tokens()

    return token_response.by_resource_server


def get_confidential_app_authorizer(client_id, client_secret):
    tokens = do_client_credentials_app_authentication(
            client_id=client_id,
            client_secret=client_secret)
    transfer_tokens = tokens['transfer.api.globus.org']
    transfer_access_token = transfer_tokens['access_token']

    return globus_sdk.AccessTokenAuthorizer(transfer_access_token)


def share_data(args):

    user_source_endpoint = args.source_endpoint or source_endpoint
    user_shared_endpoint = args.shared_endpoint or shared_endpoint

    user_source_path = args.source_path or source_path
    user_destination_path = args.destination_path or destination_path
    if not user_source_path.startswith('/'):
        eprint('Source path must be absolute')
        sys.exit(1)
    if not user_destination_path.startswith('/'):
        eprint('Destination path must be absolute')
        sys.exit(1)

    if args.auth == 'native':
        # get an authorizer if it is a Native App
        authorizer = get_native_app_authorizer(client_id=CLIENT_ID)
    elif args.auth == 'client-credentials':
        secret = args.client_secret or CLIENT_SECRET
        if not secret:
            eprint('--auth client-credentials chosen, but no secret provided!'
                   ' Set "--client-secret <your secret>"'
                   )
            sys.exit(1)
        # get an authorizer if it is a Confidential App
        authorizer = get_confidential_app_authorizer(
            client_id=CLIENT_ID,
            client_secret=secret
        )
    else:
        raise ValueError('Invalid Authenticator, this script only understands '
                         'Native and Client Credential')

    # create a TransferClient object
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    # check if a destination directory exists at all
    try:
        tc.operation_ls(user_shared_endpoint, path=user_destination_path)
    except TransferAPIError as e:
        eprint(e)
        sys.exit(1)

    dirname, leaf = os.path.split(user_source_path)
    if leaf == '':
        _, leaf = os.path.split(dirname)
    destination_directory = os.path.join(user_destination_path, leaf) + '/'

    """
    check if a directory with the same name was already transferred to the
    destination path if it was and --delete option is specified, delete the
    directory
    """
    try:
        tc.operation_ls(user_shared_endpoint, path=destination_directory)
        if not args.delete:
            eprint('Destination directory exists. Delete the directory or '
                   'use --delete option')
            sys.exit(1)
        print('Destination directory, {}, exists and will be deleted'
              .format(destination_directory))
        ddata = globus_sdk.DeleteData(
                tc,
                user_shared_endpoint,
                label='Share Data Example',
                recursive=True)
        ddata.add_item(destination_directory)
        print('Submitting a delete task')
        task = tc.submit_delete(ddata)
        print('\ttask_id: {}'.format(task['task_id']))
        tc.task_wait(task['task_id'])
    except TransferAPIError as e:
        if e.code != u'ClientError.NotFound':
            eprint(e)
            sys.exit(1)

    # create a destination directory
    try:
        print('Creating destination directory {}'
              .format(destination_directory))
        tc.operation_mkdir(user_shared_endpoint, destination_directory)
    except TransferAPIError as e:
            eprint(e)
            sys.exit(1)

    # grant group/user read access to the destination directory
    if args.user_uuid:
        rule_data = {
            "DATA_TYPE": "access",
            "principal_type": "identity",
            "principal": args.user_uuid,
            "path": destination_directory,
            "permissions": "r",
        }

        try:
            print('Granting user, {}, read access to the destination directory'
                  .format(args.user_uuid))
            tc.add_endpoint_acl_rule(user_shared_endpoint, rule_data)
        except TransferAPIError as e:
            if e.code != u'Exists':
                eprint(e)
                sys.exit(1)

    if args.group_uuid:
        rule_data = {
            "DATA_TYPE": "access",
            "principal_type": "group",
            "principal": args.group_uuid,
            "path": destination_directory,
            "permissions": "r",
        }

        try:
            print('Granting group, {}, read access to '.format(args.user_uuid))
            tc.add_endpoint_acl_rule(user_shared_endpoint, rule_data)
        except TransferAPIError as e:
            if e.code != u'Exists':
                eprint(e)
                sys.exit(1)

    # transfer data - source directory recursively
    tdata = globus_sdk.TransferData(
            tc,
            user_source_endpoint,
            user_shared_endpoint,
            label='Share Data Example')
    tdata.add_item(user_source_path, destination_directory, recursive=True)
    try:
        print('Submitting a transfer task')
        task = tc.submit_transfer(tdata)
    except TransferAPIError as e:
        eprint(e)
        sys.exit(1)
    print('\ttask_id: {}'.format(task['task_id']))
    print('You can monitor the transfer task programmatically using Globus SDK'
          ', or go to the Web UI, https://www.globus.org/app/activity/{}.'
          .format(task['task_id']))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Copy data from your private endpoint to a shared one for'
        'other people to access. You can share data with both individual users'
        ' and groups.'
    )
    parser.add_argument(
        '--source-endpoint',
        required=bool(not source_endpoint),
        help='Source Endpoint UUID where your data is stored.'
    )
    parser.add_argument(
        '--shared-endpoint',
        required=bool(not shared_endpoint),
        help='The place you will share your data. Create a shared endpoint '
             'by going to globus.org/app/transfer, navigating to your endpoint'
             ' and clicking "share" on a folder.'
    )
    parser.add_argument(
        '--source-path',
        required=bool(not source_path),

    )
    parser.add_argument(
        '--destination-path',
        required=bool(not destination_path)
    )
    parser.add_argument(
            '--group-uuid',
            help='UUID of a group transferred data will be shared with')
    parser.add_argument(
            '--user-uuid',
            help='UUID of a user transferred data will be shared with')
    parser.add_argument(
            '--delete', action='store_true',
            help='Delete a destination directory if already exists before '
            'transferring data')
    parser.add_argument('--auth', choices=APP_AUTHENTICATORS,
                        default=AUTHENTICATION)
    parser.add_argument('--client-secret')
    args = parser.parse_args()

    share_data(args)
