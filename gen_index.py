#!/usr/bin/env python

"""
Recursively list all directories on a shared endpoint, generate
a index.html file for each directory, and upload the index.html files.
Globus HTTPS server does not provide directory listing, so the index.html
file can be used to see content of the shared endpoint via the Globus HTTPS
server associated with the shared endpoint.

Required:
Register your own app at developers.globus.org. Configure as follows:
Native App:
    * "Redirect URLs" -- Set to "https://auth.globus.org/v2/web/auth-code".
        You can setup your own server for distributing auth codes if you wish.
    * Scopes:
        Can be left empty.
    * Check "Native App".
"""

from __future__ import print_function
import os
import sys
import argparse
import json
import datetime
import shutil
import globus_sdk
from globus_sdk.exc import TransferAPIError, GlobusTimeoutError
from native_login import NativeClient

# Native App requires Client IDs. Create your app at developers.globus.org.
# The following id is for testing only and should not be relied upon (You
# should create your own app).
CLIENT_ID = '079bdf4e-9666-4816-ac01-7eab9dc82b93'

APP_NAME = 'My App'

# Redirect URI specified when registering a native app
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'

# For this example, we will be liberal with scopes.
SCOPES = ('openid '
          'urn:globus:auth:scope:transfer.api.globus.org:all')

TOKEN_FILE = 'refresh-tokens.json'

# Example: CODAR shared endpoint
shared_endpoint = '97235036-3749-11e7-bcdc-22000b9a448b'

# Globus Connect Personal Endpoint set up locally
local_endpoint = ''
local_index_dir = 'tmp'

# Images and HTML templates needed to create HTML index files
back_gif = (
    'R0lGODlhFAAWAMIAAP///8z//5mZmWZmZjMzMwAAAAAAAAAAACH+TlRoaXMgYXJ0IGlzIGlu'
    'IHRoZSBwdWJsaWMgZG9tYWluLiBLZXZpbiBIdWdoZXMsIGtldmluaEBlaXQuY29tLCBTZXB0'
    'ZW1iZXIgMTk5NQAh+QQBAAABACwAAAAAFAAWAAADSxi63P4jEPJqEDNTu6LO3PVpnDdOFnaC'
    'kHQGBTcqRRxuWG0v+5LrNUZQ8QPqeMakkaZsFihOpyDajMCoOoJAGNVWkt7QVfzokc+LBAA7'
)

folder_gif = (
    'R0lGODlhFAAWAMIAAP/////Mmcz//5lmMzMzMwAAAAAAAAAAACH+TlRoaXMgYXJ0IGlzIGlu'
    'IHRoZSBwdWJsaWMgZG9tYWluLiBLZXZpbiBIdWdoZXMsIGtldmluaEBlaXQuY29tLCBTZXB0'
    'ZW1iZXIgMTk5NQAh+QQBAAACACwAAAAAFAAWAAADVCi63P4wyklZufjOErrvRcR9ZKYpxUB6'
    'aokGQyzHKxyO9RoTV54PPJyPBewNSUXhcWc8soJOIjTaSVJhVphWxd3CeILUbDwmgMPmtHrN'
    'IyxM8Iw7AQA7'
)

file_gif = (
    'R0lGODlhFAAWAMIAAP///8z//8zMzJmZmTMzMwAAAAAAAAAAACH+TlRoaXMgYXJ0IGlzIGlu'
    'IHRoZSBwdWJsaWMgZG9tYWluLiBLZXZpbiBIdWdoZXMsIGtldmluaEBlaXQuY29tLCBTZXB0'
    'ZW1iZXIgMTk5NQAh+QQBAAABACwAAAAAFAAWAAADaUi6vPEwEECrnSS+WQoQXSEAE6lxXgeo'
    'pQmha+q1rhTfakHo/HaDnVFo6LMYKYPkoOADim4VJdOWkx2XvirUgqVaVcbuxCn0hKe04znr'
    'IV/ROOvaG3+z63OYO6/uiwlKgYJJOxFDh4hTCQA7'
)

html_header = ''.join([
    '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <html>
    <head><title>Index of {directory}</title></head>
    <style>
        .back {{
            background: url(data:image/gif;base64,''',
    back_gif,
    ''') no-repeat;
        }}
        .folder {{
            background: url(data:image/gif;base64,''',
    folder_gif,
    ''') no-repeat;
        }}
        .file {{
            background: url(data:image/gif;base64,''',
    file_gif,
    ''') no-repeat;
        }}
        .icon {{
            width: 20px;
            height: 24px;
        }}
    </style>
    <body>
    <h1>Index of {directory}</h1>
    <table>
        <tr><th></th><th>Name</th><th>Last modified</th><th>Size</th></tr>
        <tr><th colspan="4"><hr></th></tr>
    '''
])

folder_row = '''
        <tr>
            <td class="icon folder"></td>
            <td><a href="{name}/index.html">{name}</a> </td>
            <td align="right">{tstamp} </td>
            <td>-</td>
        </tr>
'''

file_row = '''
        <tr>
            <td class="icon file"></td>
            <td><a href="{name}">{name} </a></td>
            <td align="right">{tstamp} </td>
            <td align="right">{size}</td>
        </tr>
'''

html_footer = '''
        <tr><th colspan="4"><hr></th></tr>
    </table>
    Globus HTTPS Server at ALCF/ANL Petrel; index generated on {}
    </body>
    </html>
'''

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
    args_list = list(args)
    args_list[0] = '\033[0;31m{}\033[0m'.format(args_list[0])
    new_args = tuple(args_list)
    print(*new_args, file=sys.stderr, **kwargs)


def get_native_app_authorizer(client_id):
    tokens = None
    client = NativeClient(client_id=client_id, app_name=APP_NAME)
    try:
        # if we already have tokens, load and use them
        tokens = load_tokens_from_file(TOKEN_FILE)
    except:
        pass

    if not tokens:
        tokens = client.login(requested_scopes=SCOPES,
                              refresh_tokens=True)
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


def get_human_readable_size(size):
    suffixes = ['', 'K', 'M', 'G', 'T', 'P']
    for i in range(len(suffixes)):
        if size / 1000.0 < 1.0:
            break
        size = size / 1024.0
    suffix = suffixes[i]
    if size < 10.0 and i > 0:
        return '{:.1f}{}'.format(size, suffix)
    else:
        return '{}{}'.format(int(size), suffix)


def create_index(directory, files, catalog):

    html = html_header.format(directory=directory)
    if directory != '/':
        html += ('<tr><td class="icon back"></td>'
                 '<td><a href="../index.html">Parent Directory</a></td></tr>')
        try:
            os.makedirs(local_index_dir + directory)
        except OSError:
            # Already exists
            pass
    for item in files:
        name = item['name']
        if name.startswith('.') or name == 'index.html':
            continue
        if item['type'] == 'dir':
            html += folder_row.format(
                    name=item['name'],
                    tstamp=item['last_modified'])
        elif item['type'] == 'file':
            html += file_row.format(
                    name=item['name'],
                    tstamp=item['last_modified'],
                    size=get_human_readable_size(item['size']))
            catalog.append({'dir': directory, 'file': item })
    html += html_footer.format(
            datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M'))

    with open(local_index_dir + directory + '/index.html', 'w') as index_file:
        index_file.write(html)


def walk(tc, shared_endpoint, directory, catalog):
    while True:
        try:
            r = tc.operation_ls(shared_endpoint, path=directory)
            break
        except (TransferAPIError, GlobusTimeoutError) as e:
            eprint(e)
    for item in r['DATA']:
        if item['type'] == 'dir' and not item['name'].startswith('.'):
            path = os.path.join(directory, item['name'])
            print(path)
            walk(tc, shared_endpoint, path, catalog)

    create_index(directory, r['DATA'], catalog)


def upload(tc, local_endpoint, shared_endpoint):
    # transfer data - local directory recursively
    print("Creating a transfer task with all index.html files...")
    tdata = globus_sdk.TransferData(
            tc,
            local_endpoint,
            shared_endpoint,
            label='Upload index html files')
    cwd = os.getcwd()
    for root, dirs, files in os.walk(local_index_dir):
        if 'index.html' in files:
            local_path = os.path.join(cwd, root, 'index.html')
            shared_path = os.path.join(root.replace(local_index_dir, '/'), 'index.html')
            print('{}:{} -> {}:{}'.format(local_endpoint, local_path, shared_endpoint, shared_path))
            tdata.add_item(local_path, shared_path)
    try:
        print('Submitting a transfer task...')
        task = tc.submit_transfer(tdata)
    except TransferAPIError as e:
        eprint(e)
        sys.exit(1)
    print('\ttask_id: {}'.format(task['task_id']))
    print('You can monitor the transfer task programmatically using Globus SDK'
          ', or go to the Web UI, https://www.globus.org/app/activity/{}.'
          .format(task['task_id']))


def generate_index(args):

    catalog = []

    shutil.rmtree(local_index_dir, ignore_errors=True)
    os.mkdir(local_index_dir)

    shared_ept = args.shared_endpoint or shared_endpoint
    if not shared_ept:
        eprint('Invalid shared endpoint')
        sys.exit(1)

    local_ept = args.local_endpoint or local_endpoint
    if not local_ept:
        eprint('Invalid local endpoint')
        sys.exit(1)

    authorizer = get_native_app_authorizer(client_id=CLIENT_ID)

    # create a TransferClient object
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    # list all directories on the shared endpoint recursively
    # and generate index.html files locally in tmp/
    print('Generating index.html files recursively...')
    walk(tc, shared_ept, args.directory, catalog)

    # upload all index.html from tmp/ to the shared endpoint
    # upload(tc, local_ept, shared_ept)

    f = open('index.json', 'w')
    json.dump(catalog, f)
    f.close()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Recursively list all directories on a shared endpoint,'
        ' generate index.html file for each directory, and upload the'
        ' index.html to the Globus HTTPS server associated with the shared'
        ' endpoint.'
    )
    parser.add_argument(
        '--shared-endpoint',
        help='Shared Endpoint UUID where your data is stored.'
    )
    parser.add_argument(
        '--local-endpoint',
        help='Local Endpoint UUID that points to the system you are running the script on.'
    )
    parser.add_argument(
            '--directory', default='/',
            help='A directory to start with. By default, it will start from'
            ' the root "/".')
    args = parser.parse_args()

    generate_index(args)
