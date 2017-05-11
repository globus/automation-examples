#!/usr/bin/env python

import json
import sys
import webbrowser
import os

from globus_sdk import (NativeAppAuthClient, TransferClient,
                        RefreshTokenAuthorizer, TransferData)
from globus_sdk.exc import GlobusAPIError, TransferAPIError

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

SOURCE_ENDPOINT = 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'
DESTINATION_ENDPOINT = 'ddb59af0-6d04-11e5-ba46-22000b92c6ec'
# Sample data
SOURCE_PATH = '/share/godata/'

# Destination Path
# The directory will be created if it doesn't exist
DESTINATION_PATH = '/~/sync-demo'

CLIENT_ID = '079bdf4e-9666-4816-ac01-7eab9dc82b93'
DATA_FILE = 'transfer-data.json'
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
SCOPES = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')

TUTORIAL_ENDPOINT_ID = 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'
PREVIOUS_TASK_RUN_CASES = ['SUCCEEDED', 'FAILED']


get_input = getattr(__builtins__, 'raw_input', input)


def do_native_app_authentication(client_id, redirect_uri,
                                 requested_scopes=None):
    """
    Does a Native App authentication flow and returns a
    dict of tokens keyed by service name.
    """
    client = NativeAppAuthClient(client_id=client_id)
    # pass refresh_tokens=True to request refresh tokens
    client.oauth2_start_flow(requested_scopes=requested_scopes,
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


def load_data_from_file(filepath):
    """Load a set of saved tokens."""
    with open(filepath, 'r') as f:
        tokens = json.load(f)

    return tokens


def save_data_to_file(filepath, key, data):
    """Save data to a file"""
    try:
        store = load_data_from_file(filepath)
    except:
        store = {}
    store[key] = data
    with open(filepath, 'w') as f:
        json.dump(store, f)


def update_tokens_file_on_refresh(token_response):
    """
    Callback function passed into the RefreshTokenAuthorizer.
    Will be invoked any time a new access token is fetched.
    """
    save_data_to_file(DATA_FILE, 'tokens', token_response.by_resource_server)


def get_tokens():
    tokens = None
    try:
        # if we already have tokens, load and use them
        tokens = load_data_from_file(DATA_FILE)['tokens']
    except:
        pass

    if not tokens:
        # if we need to get tokens, start the Native App authentication process
        tokens = do_native_app_authentication(CLIENT_ID, REDIRECT_URI, SCOPES)

        try:
            save_data_to_file(DATA_FILE, 'tokens', tokens)
        except:
            pass
    return tokens


def is_remote_session():
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


def setup_transfer_client(transfer_tokens):

    authorizer = RefreshTokenAuthorizer(
        transfer_tokens['refresh_token'],
        NativeAppAuthClient(client_id=CLIENT_ID),
        access_token=transfer_tokens['access_token'],
        expires_at=transfer_tokens['expires_at_seconds'],
        on_refresh=update_tokens_file_on_refresh)

    transfer_client = TransferClient(authorizer=authorizer)

    # print out a directory listing from an endpoint
    try:
        transfer_client.endpoint_autoactivate(SOURCE_ENDPOINT)
        transfer_client.endpoint_autoactivate(DESTINATION_ENDPOINT)
    except GlobusAPIError as ex:
        print(ex)
        if ex.http_status == 401:
            sys.exit('Refresh token has expired. '
                     'Please delete refresh-tokens.json and try again.')
        else:
            raise ex
    return transfer_client


def check_source_folder(transfer_client, source_ep, source_path):
    """Check that source is a directory"""
    try:
        transfer_client.operation_ls(source_ep, path=source_path)
    except TransferAPIError as tapie:
        print('Failed to query source endpoint "{}": {}'.format(
            source_ep,
            tapie.message
        ))
        sys.exit(1)


def check_destination_folder(transfer_client, dest_ep, dest_path):

    try:
        transfer_client.operation_ls(dest_ep)
    except TransferAPIError:
        print('Could not query destination endpoint,'
              ' is it setup as a shared endpoint?')
        sys.exit(1)
    try:
        transfer_client.operation_ls(dest_ep, path=dest_path)
    except TransferAPIError:
        try:
            transfer_client.operation_mkdir(dest_ep, dest_path)
            print('Created directory: {}'.format(dest_path))
        except TransferAPIError as tapie:
            print('Failed to start transfer: {}'.format(tapie.message))
            sys.exit(1)


def main():

    tokens = get_tokens()
    transfer = setup_transfer_client(tokens['transfer.api.globus.org'])

    try:
        task_data = load_data_from_file(DATA_FILE)['task']
        task = transfer.get_task(task_data['task_id'])
        if task['status'] not in PREVIOUS_TASK_RUN_CASES:
            print('The last transfer status is {}, skipping run...'.format(
                task['status']
            ))
            sys.exit(1)
    except KeyError:
        # Ignore if there is no previous task
        pass

    check_source_folder(transfer, SOURCE_ENDPOINT, SOURCE_PATH)
    check_destination_folder(transfer, DESTINATION_ENDPOINT, DESTINATION_PATH)

    tdata = TransferData(
        transfer,
        SOURCE_ENDPOINT,
        DESTINATION_ENDPOINT,
        label="SDK example",
        sync_level="checksum"
    )
    tdata.add_item(SOURCE_PATH, DESTINATION_PATH, recursive=True)

    task = transfer.submit_transfer(tdata)
    save_data_to_file(DATA_FILE, 'task', task.data)
    print('Transfer has been started from {}:{} to {}:{}'.format(
        SOURCE_ENDPOINT,
        SOURCE_PATH,
        DESTINATION_ENDPOINT,
        DESTINATION_PATH
    ))


if __name__ == '__main__':
    main()
