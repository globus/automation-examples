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
import tika
from tika import parser
from globus_sdk.exc import TransferAPIError, GlobusTimeoutError
from fair_research_login import NativeClient

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
        <tr><th></th><th>Name (path)</th><th>Last modified</th><th>Size</th></tr>
        <tr><th colspan="4"><hr></th></tr>
    '''
])

folder_row = '''
        <tr>
            <td class="icon folder"></td>
            <td>{name} ({directory})</td>
            <td align="right">{tstamp} </td>
            <td>-</td>
        </tr>
'''

file_row = '''
        <tr>
            <td class="icon file"></td>
            <td>{name} ({directory})</td>
            <td align="right">{tstamp} </td>
            <td align="right">{size}</td>
        </tr>
'''

folder_row_recur = '''
        <tr>
            <td class="icon folder"></td>
            <td><a href="{name}/index.html">{name}</a> </td>
            <td align="right">{tstamp} </td>
            <td>-</td>
        </tr>
'''

file_row_recur = '''
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

markdown_title = ''.join([
'''
# Index of {directory}
'''
])

markdown_section = '''
## {name}
**Type**: {item_type}
**Location**: {directory}
**Last Modified**: {tstamp}
**Size**: {size}
'''

markdown_footer = '''
#### Globus HTTPS Server at ALCF/ANL Petrel; index generated on {}
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
    return '{}{}'.format(int(size), suffix)


def create_index(catalog, directory, filtered_names):
    """
    Creates non-recursive (single) index.html index file.
    """
    html = html_header.format(directory=directory)
##    if directory != '/' and args.html_output:
##        html += ('<tr><td class="icon back"></td>'
##                 '<td><a href="../index.html">Parent Directory</a></td></tr>')
##        try:
##            os.makedirs(local_index_dir + directory)
##        except OSError:
##            # Already exists
##            pass
    for item in catalog:
        file_data = item['file']
        html = update_html(html, item, file_data, filtered_names)
        name = file_data['name']
        directory = item['dir']
        if file_data['type'] == 'dir':
            if name in filtered_names:
                html += folder_row.format(name=name,
                                          directory=directory,
                                          tstamp=file_data['last_modified'])
        if file_data['type'] == 'file':
            if filter_item(name, directory) and len(args.include_filter) > 0:
                if not filter_item(name, directory, 1):
                    html += file_row.format(name=name,
                                            directory=directory,
                                            tstamp=file_data['last_modified'],
                                            size=get_human_readable_size(file_data['size']))
                    if not name.startswith('index.'):
                        download_file(directory, name)
            elif not filter_item(name, directory, 1):
                html += file_row.format(name=name,
                                        directory=directory,
                                        tstamp=file_data['last_modified'],
                                        size=get_human_readable_size(file_data['size']))

    html += html_footer.format(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M'))

    if args.html_output and directory == '/':
        with open(local_index_dir + directory + '/index.html', 'w') as index_file:
            index_file.write(html)




def update_html(html, item, data, filtered_names):
    name = data['name']
    directory = item['dir']
    if data['type'] == 'dir':
        if name in filtered_names:
            html += folder_row.format(name=name,
                                      directory=directory,
                                      tstamp=data['last_modified'])
    if data['type'] == 'file':
        if filter_item(name, directory):
            if not filter_item(name, directory, 1):
                html += file_row.format(name=name,
                                        directory=directory,
                                        tstamp=data['last_modified'],
                                        size=get_human_readable_size(data['size']))
            elif not filter_item(name, directory, 1):
                html += file_row.format(name=name,
                                        directory=directory,
                                        tstamp=data['last_modified'],
                                        size=get_human_readable_size(data['size']))

    return html


def create_recur_index(directory, data, catalog):

    # separate original data and filtered data
    files = data['orig_data']
    filtered_names = data['filtered_names']

    html = html_header.format(directory=directory)
    if directory != '/' and args.html_output:
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
            if item['name'] in filtered_names:
                html += folder_row_recur.format(name=item['name'],
                                          tstamp=item['last_modified'])
        if item['type'] == 'file':
            if filter_item(name, directory):
                if not filter_item(name, directory, 1):
                    html += file_row_recur.format(name=item['name'],
                                            tstamp=item['last_modified'],
                                            size=get_human_readable_size(item['size']))
            elif not filter_item(name, directory, 1):
                html += file_row_recur.format(name=item['name'],
                                        tstamp=item['last_modified'],
                                        size=get_human_readable_size(item['size']))
            
        if item['name'] not in args.exclude_filter:
            catalog.append({'dir': directory, 'file': item})

    html += html_footer.format(
        datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M'))
    
    if args.html_output:
        with open(local_index_dir + directory + '/index.html', 'w') as index_file:
            index_file.write(html)


def walk(tc, shared_endpoint, directory, catalog):
    while True:
        try:
            r = tc.operation_ls(shared_endpoint, path=directory)
            break
        except (TransferAPIError, GlobusTimeoutError) as e:
            eprint(e)

    filtered_names = []
    filtered_data = []
    result = {}
    for item in r['DATA']:
        name = item['name']
        if item['type'] == 'dir' and not name.startswith('.'):
            if filter_item(name, directory) and len(args.include_filter) > 0:
                if not filter_item(name, directory, 1):
                    filtered_names.append(name)
                    filtered_data.append({'dir': directory, 'file': item})
                    path = os.path.join(directory, name)
                    print(path)
                    result = walk(tc, shared_endpoint, path, catalog)
            elif not filter_item(name, directory, 1):
                filtered_names.append(name)
                filtered_data.append({'dir': directory, 'file': item})
                path = os.path.join(directory, name)
                print(path)
                result = walk(tc, shared_endpoint, path, catalog)
            else:
                filtered_names.append(name)
                filtered_data.append({'dir': directory, 'file': item})
                path = os.path.join(directory, name)
                print(path)
                result = walk(tc, shared_endpoint, path, catalog)
        elif item['type'] == 'file':
            if filter_item(name, directory) and len(args.include_filter) > 0:
                if not filter_item(name, directory, 1):
                    filtered_names.append(name)
                    filtered_data.append({'dir': directory, 'file': item})
            elif not filter_item(name, directory, 1):
                filtered_names.append(name)
                filtered_data.append({'dir': directory, 'file': item})
            else:
                filtered_names.append(name)
                filtered_data.append({'dir': directory, 'file': item})
        if result != {}:
            result_data = result['items']
            result_names = result['names']
            for filtered in result_data:
                if filtered not in filtered_data:
                    filtered_data.append(filtered)
            for filtered in result_names:
                if filtered not in filtered_names:
                    filtered_names.append(filtered)

    data = {'orig_data':r['DATA'], 'filtered_names':filtered_names}
    if not args.recursive:
        for data in filtered_data:
            catalog.append(data)
        create_index(catalog, directory, filtered_names)
    else:
        create_recur_index(directory, data, catalog)


    return {'names': filtered_names, 'items': filtered_data}
    
def filter_item(item_name, directory, filter_type=0):
    """
    Check if the given item (a file or directory) should be included/excluded.
    Decision is based on the respective filter (include/exclude), which is specified
    by the given filter_type. If filter_type is 0 (default value) then the include
    filter will be checked against, otherwise the exclude_filter will be used.
    """
    # check which filter to use
    filters = None
    if filter_type:
        filters = args.exclude_filter
    else:
        filters = args.include_filter

    is_sub_dir = False
    for name in filters:
        if name in directory:
            is_sub_dir = True
        
    for name in filters:
        if name.find('/') > 0:
            names = name.split('/')
            if item_name in names or is_sub_dir:
                return True
        elif item_name in name or is_sub_dir:
            return True

    return False


def upload(tc, local_endpoint, shared_endpoint):
    # transfer data - local directory recursively
    print("Creating a transfer task with all index.html and index.md files...")
    tdata = None
    if args.dest_endpoint and args.dest_path:
        tdata = globus_sdk.TransferData(tc,
                                        local_endpoint,
                                        args.dest_endpoint,
                                        label='Upload index html and markdown files')
        cwd = os.getcwd()
        for root, dirs, files in os.walk(local_index_dir):
            if 'index.html' in files:
                local_path = os.path.join(cwd, root, 'index.html')
                dest_path = os.path.join(root.replace(local_index_dir, '/'), 'index.html')
                print('{}:{} -> {}:{}'.format(local_endpoint,
                                              local_path,
                                              args.dest_endpoint,
                                              dest_path))
                tdata.add_item(local_path, dest_path)
            if 'index.md' in files:
                local_path = os.path.join(cwd, root, 'index.md')
                dest_path = os.path.join(root.replace(local_index_dir, '/'), 'index.md')
                print('{}:{} -> {}:{}'.format(local_endpoint,
                                              local_path,
                                              args.dest_endpoint,
                                              dest_path))
                tdata.add_item(local_path, dest_path)
    else:
        tdata = globus_sdk.TransferData(tc,
                                        local_endpoint,
                                        shared_endpoint,
                                        label='Upload index html and markdown files')
        cwd = os.getcwd()
        for root, dirs, files in os.walk(local_index_dir):
            if 'index.html' in files:
                local_path = os.path.join(cwd, root, 'index.html')
                shared_path = os.path.join(root.replace(local_index_dir, '/'), 'index.html')
                print('{}:{} -> {}:{}'.format(local_endpoint,
                                              local_path,
                                              shared_endpoint,
                                              shared_path))
                tdata.add_item(local_path, shared_path)
            if 'index.md' in files:
                local_path = os.path.join(cwd, root, 'index.md')
                shared_path = os.path.join(root.replace(local_index_dir, '/'), 'index.md')
                print('{}:{} -> {}:{}'.format(local_endpoint,
                                              local_path,
                                              shared_endpoint,
                                              shared_path))
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


def generate_index():

    catalog = []

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

    # if HTML and/or Markdown index file was requested, need to create empty temp directory
    if args.html_output or args.markdown_output:
        shutil.rmtree(local_index_dir, ignore_errors=True)
        os.mkdir(local_index_dir)

    # list all directories on the shared endpoint recursively
    # and generate index.html and index.md files locally in tmp/ (if requested)
    filtered = walk(tc, shared_ept, args.directory, catalog)

    if not args.no_json:
        f = open('index.json', 'w')
        json.dump(catalog, f)
        f.close()
    
    if args.markdown_output:
        md_path = local_index_dir
        if args.directory != '/':
            md_path += args.directory + '/index.md'
        else:
            md_path += 'index.md'
        with open(local_index_dir + args.directory + '/index.md', 'w') as markdown_file:
            path = args.directory
            markdown = markdown_title.format(directory=path)
            for item in catalog:
                file_item = item['file']
                markdown += markdown_section.format(name=file_item['name'],
                                                    item_type=file_item['type'],
                                                    directory=item['dir'],
                                                    tstamp=file_item['last_modified'],
                                                    size=get_human_readable_size(file_item['size']))
            markdown += markdown_footer.format(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M'))
            markdown_file.write(markdown)

    if args.html_output or args.markdown_output:
        # upload all index files from tmp/ to the shared endpoint
        upload(tc, local_ept, shared_ept)

    if args.simple_parser:
        print('Getting the files and directories to parse:')
        tdata = globus_sdk.TransferData(tc,
                                        destination_endpoint=local_ept,
                                        source_endpoint=shared_ept,
                                        label='Downloading from Shared to Local')
        download_data(tc, tdata, shared_ept, args.directory)
        try:
            print('\nSubmitting a transfer task...')
            task = tc.submit_transfer(tdata)
            completed = tc.task_wait(task["task_id"], timeout=600, polling_interval=15)
            if completed:
                print('\ttask_id: {}'.format(task['task_id']))
                print('You can monitor the transfer task programmatically using Globus SDK'
                      ', or go to the Web UI, https://www.globus.org/app/activity/{}.'
                      .format(task['task_id']))
                print('\nStarting the Simple Parser:')
                local_path = os.path.join(os.getcwd(), local_index_dir)
                parsed_data = parse_files(tc,
                                          local_ept,
                                          local_path,
                                          filtered['names'])

                f = open('parsed_results.json', 'w')
                json.dump(parsed_data, f)
                f.close()
            else:
                print("Transfer task failed to complete within 10 minutes")
        except TransferAPIError as e:
            eprint(e)
            sys.exit(1)


def download_data(tc, tdata, shared_ept, directory):
    """
    Downloads the data from the given shared endpoint (and directory) to
    the local/current endpoint and directory. Does not currently support
    the include/exclude filters.
    """
    cwd = os.getcwd()
    local_path = os.path.join(cwd, local_index_dir)
    tdata.add_item(directory, local_path, recursive=True)


def parse_files(tc, endpoint, directory, filtered_names):
    os.environ["TIKA_SERVER_ENDPOINT"] = endpoint

    items = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            if not name.startswith('.') and name in filtered_names:
                path = os.path.join(root, name)
                parsed = parser.from_file(path)
                if 'metadata' in parsed.keys():
                    items.append(parsed['metadata'])
        for name in dirs:
            if not name.startswith('.') and name in filtered_names:
                path = os.path.join(root, name)
                items = items + parse_files(tc,
                                            endpoint,
                                            path,
                                            filtered_names)
    return items
        
    
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Recursively list all directories on a shared endpoint,'
        ' generate index.html file for each directory, and upload the'
        ' index.html to the Globus HTTPS server associated with the shared'
        ' endpoint.'
    )
    arg_parser.add_argument(
        '--shared-endpoint',
        help='Shared Endpoint UUID where your data is stored.'
    )
    arg_parser.add_argument(
        '--local-endpoint',
        help='Local Endpoint UUID that points to the system you are running the script on.'
    )
    arg_parser.add_argument(
        '--directory', default='/',
        help='A directory to start with. By default, it will start from the root "/".')
    arg_parser.add_argument(
        '--no-json', action='store_true', default=False,
        help='Writes the results to to a JSON file. Include this flag if you do not want'
        ' the file.')
    arg_parser.add_argument(
        '--html-output', action='store_true', default=False,
        help='Writes the results to a HTML file and stores files and subdirectories in a'
        ' specified location (see "dest-path argument for details"). Disabled by default,'
        ' include this flag if you want the file.')
    arg_parser.add_argument(
        '--markdown-output', action='store_true', default=False, 
        help='Writes the results to a Markdown file. Disabled by default, include this flag'
        ' if you want the file.')
    arg_parser.add_argument(
        '--recursive', action='store_true', default=False,
        help='Changes the behavior of the script so that the data is split into several'
        ' (recursive) index files instead of a single large index file.')
    arg_parser.add_argument(
        '--dest-endpoint', default=None,
        help='Endpoint UUID that you want your data to be uploaded to. The default'
        ' UUID is the shared-endpoint. Only specify if you do not want the data to be'
        ' uploaded to the shared endpoint. If you use this argument, you must also specify a valid'
        ' path (see dest-path).')
    arg_parser.add_argument(
        '--dest-path', default=None,
        help='The path in the specified that you want your data to be uploaded to. The default'
        ' location is the shared-endpoint. Only specify if you do not want the data to be'
        ' uploaded to the shared endpoint. If you use this argument, you must also specify a valid'
        ' UUID (see dest-endpoint).')
    arg_parser.add_argument(
        '--include-filter', nargs='+', default=[],
        help='A filter that specifies certain files or directories that you want included from'
        ' the list. Should be space-separated and files should include extensions. Example: to'
        ' include file "f1.txt" and directory "files" you would provide this flag with:'
        ' "f1.txt files".')
    arg_parser.add_argument(
        '--exclude-filter', nargs='+', default=[],
        help='A filter that specifies certain files that you want excluded from the list.'
        ' Should be space-separated and files should include extensions. Example: to exclude file'
        ' "f1.txt" and directory "files" you would provide this flag with: "f1.txt files". If you'
        ' want the names to be separated by a different delimiter (i.e., comma-separated) see the'
        ' "filter-delimiter" flag.')
    arg_parser.add_argument(
        '--pattern-filter', action='store_true', default=False,
        help='By default, the (include and exclude) filters check for exact matches. This flag'
        ' changes that behavior so that the filters use pattern matching. Best used when you'
        ' want to include/exclude all files/folders of a particular type or with a particular'
        ' name (e.g., excluding all files that end in ".txt").')
    arg_parser.add_argument(
        '--simple-parser', action='store_true', default=False,
        help='Enables a simple parser that extracts more metadata, but takes longer to run.')
    args = arg_parser.parse_args()

    no_output = args.no_json and not(args.html_output or args.markdown_output)
    if no_output:
        print("No index file type specified.")
    else:
        generate_index()        
