#!/usr/bin/python
from __future__ import print_function

import sys
import globus_sdk

# you must have a client ID
CLIENT_ID = ''
# your app's client secret
CLIENT_SECRET = ''

def sanity_check():
    if not bool(CLIENT_ID and CLIENT_SECRET):
        print('Please create an app at developers.globus.org and add the client id and secret')
        sys.exit(1)

    if not destination_endpoint:
        print('Please include a shared endpoint destination')
        sys.exit(1)


def setup_transfer_client():
    client = globus_sdk.ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)
    token_response = client.oauth2_client_credentials_tokens()
    # wrap the token in an object that implements the globus_sdk.GlobusAuthorizer interface
    # in this case, an AccessTokenAuthorizer, which takes an access token and produces Bearer Auth headers
    transfer_authorizer = globus_sdk.AccessTokenAuthorizer(
        token_response.by_resource_server['transfer.api.globus.org']['access_token'])

    # create a TransferClient object which Authorizes its calls using that GlobusAuthorizer
    tc = globus_sdk.TransferClient(authorizer=transfer_authorizer)
    return tc


def check_destination(dest_ep, dest_path):

    try:
        tc.operation_ls(dest_ep)
    except globus_sdk.exc.TransferAPIError as tapie:
        print('Could not query destination endpoint, is it setup as a shared endpoint?')
        sys.exit(1)
    try:
        tc.operation_ls(dest_ep, path=dest_path)
    except globus_sdk.exc.TransferAPIError:
        try:
            tc.operation_mkdir(dest_ep, dest_path)
            print('Created directory: {}'.format(dest_path))
        except globus_sdk.exc.TransferAPIError:
            print('Failed to start transfer: has "{}" been granted write access?'.format(dest_path))
            sys.exit(1)


def recursive_directory_transfer(tc, src_ep, dest_ep, src_path, dest_path):
    tdata = globus_sdk.TransferData(tc, source_endpoint,
                     destination_endpoint,
                     label="SDK example",
                     sync_level="checksum")
    tdata.add_item(source_path, destination_path,
            recursive=True)
    transfer_result = tc.submit_transfer(tdata)

    return(transfer_result)


if __name__ == '__main__':
    sanity_check()

    # Globus Tutorial Endpoint 1
    source_endpoint = 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'
    # Globus Tutorial Endpoint 2
    destination_endpoint = 'ddb59af0-6d04-11e5-ba46-22000b92c6ec'
    # Sample data
    source_path = '/share/godata/'
    # Destination Path
    # The directory will be created if it doesn't exist
    destination_path = '/sync-demo'
    
    tc = setup_transfer_client()
    check_destination(destination_endpoint, destination_path)
    transfer_result = recursive_directory_transfer(
            tc,
            source_endpoint,
            destination_endpoint,
            source_path,
            destination_path
    )

    print('{}, the task ID is: "{}"'.format(transfer_result['message'], transfer_result['task_id']))
