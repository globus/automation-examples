from __future__ import print_function
import os
import sys
import argparse
import webbrowser
import json
import globus_sdk
from globus_sdk.exc import TransferAPIError

# you must have a client ID
CLIENT_ID = '079bdf4e-9666-4816-ac01-7eab9dc82b93'
# the secret, needed for a Confidential App
CLIENT_SECRET = ''
# Redirect URI specified when registering a native app
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
SCOPES = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')
TOKEN_FILE = 'refresh-tokens.json'

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
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


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


def do_confidential_app_authentication(client_id, client_secret):
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
    tokens = do_confidential_app_authentication(
            client_id=client_id,
            client_secret=client_secret)
    transfer_tokens = tokens['transfer.api.globus.org']
    transfer_access_token = transfer_tokens['access_token']

    return globus_sdk.AccessTokenAuthorizer(transfer_access_token)


def share_data(args):

    if not args.source_path.startswith('/'):
        print('Source path must be absolute', file=sys.stderr)
        sys.exit(1)
    if not args.destination_path.startswith('/'):
        print('Destination path must be absolute', file=sys.stderr)
        sys.exit(1)

    # get an authorizer if it is a Native App
    authorizer = get_native_app_authorizer(client_id=CLIENT_ID)
    # get an authorizer if it is a Confidential App
    #authorizer = get_confidential_app_authorizer(client_id=CLIENT_ID,
    #        client_secret=CLIENT_SECRET)

    # create a TransferClient object
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    # check if a destination directory exists at all
    try:
        tc.operation_ls(args.shared_endpoint, path=args.destination_path)
    except TransferAPIError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    dirname, leaf = os.path.split(args.source_path)
    if leaf == '':
        _, leaf = os.path.split(dirname)
    destination_directory = os.path.join(args.destination_path, leaf) + '/'

    """
    check if a directory with the same name was already transferred to the
    destination path if it was and --delete option is specified, delete the
    directory
    """
    try:
        rc = tc.operation_ls(args.shared_endpoint, path=destination_directory)
        if not args.delete:
            print('Destination directory exists. Delete the directory or '
                  'use --delete option')
            sys.exit(1)
        print('Destination directory, {}, exists and will be deleted'
              .format(destination_directory))
        ddata = globus_sdk.DeleteData(
                tc,
                args.shared_endpoint,
                label='Share Data Example',
                recursive=True)
        ddata.add_item(destination_directory)
        print('Submitting a delete task')
        task = tc.submit_delete(ddata)
        print('\ttask_id: {}'.format(task['task_id']))
        tc.task_wait(task['task_id'])
    except TransferAPIError as e:
        if e.code != u'ClientError.NotFound':
            print(e, file=sys.stderr)
            sys.exit(1)

    # create a destination directory
    try:
        print('Creating destination directory {}'
              .format(destination_directory))
        tc.operation_mkdir(args.shared_endpoint, destination_directory)
    except TransferAPIError as e:
            print(e, file=sys.stderr)
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
            tc.add_endpoint_acl_rule(args.shared_endpoint, rule_data)
        except TransferAPIError as e:
            if e.code != u'Exists':
                print(e, file=sys.stderr)
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
            tc.add_endpoint_acl_rule(args.shared_endpoint, rule_data)
        except TransferAPIError as e:
            if e.code != u'Exists':
                print(e, file=sys.stderr)
                sys.exit(1)

    # transfer data - source directory recursively
    tdata = globus_sdk.TransferData(
            tc,
            args.source_endpoint,
            args.shared_endpoint,
            label='Share Data Example')
    tdata.add_item(args.source_path, destination_directory, recursive=True)
    try:
        print('Submitting a transfer task')
        task = tc.submit_transfer(tdata)
    except TransferAPIError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    print('\ttask_id: {}'.format(task['task_id']))
    print('You can monitor the transfer task programmatically using Globus SDK'
          ', or go to the Web UI, https://www.globus.org/app/activity/{}.'
          .format(task['task_id']))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Share data demo')
    parser.add_argument('--source-endpoint', required=True)
    parser.add_argument('--shared-endpoint', required=True)
    parser.add_argument('--source-path', required=True)
    parser.add_argument('--destination-path', required=True)
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
    args = parser.parse_args()

    share_data(args)
