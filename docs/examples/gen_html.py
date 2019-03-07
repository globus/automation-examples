#!/usr/bin/env python

"""
Generates/Updates the an HTML file that lists all of the files
in a directory.
"""

from __future__ import print_function
import os
import sys
import argparse
import shutil

# Images and HTML templates needed to create HTML index files
back_gif = (
    'R0lGODlhFAAWAMIAAP///8z//5mZmWZmZjMzMwAAAAAAAAAAACH+TlRoaXMgYXJ0IGlzIGlu'
    'IHRoZSBwdWJsaWMgZG9tYWluLiBLZXZpbiBIdWdoZXMsIGtldmluaEBlaXQuY29tLCBTZXB0'
    'ZW1iZXIgMTk5NQAh+QQBAAABACwAAAAAFAAWAAADSxi63P4jEPJqEDNTu6LO3PVpnDdOFnaC'
    'kHQGBTcqRRxuWG0v+5LrNUZQ8QPqeMakkaZsFihOpyDajMCoOoJAGNVWkt7QVfzokc+LBAA7'
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
        <tr><th></th><th>Name</th></tr>
        <tr><th colspan="2"><hr></th></tr>
    '''
])

file_row = '''
        <tr>
            <td class="icon file"></td>
            <td><a href="{directory}">{name}</a></td>
        </tr>
'''

html_footer = '''
        <tr><th colspan="2"><hr></th></tr>
    </table>
    </body>
    </html>
'''

get_input = getattr(__builtins__, 'raw_input', input)

def generate_file():
    """
    Goes through the directory and updates the HTML file.
    """
    print("\nGenerating the HTML file")
    html = html_header.format(directory=args.directory)
    for root, dirs, files in os.walk(args.directory):
        for name in files:
            print(name)
            path = os.path.join(args.directory, name)
            html += file_row.format(name=name,
                                    directory='/' + path)

    html += html_footer
    file_path = os.path.join('docs/examples/', args.file_name)
    with open(file_path, 'w') as index_file:
        index_file.write(html)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generates/Updates the an HTML file that lists all of'
        ' the files in a directory.'
    )
    parser.add_argument(
        '--directory', default='docs/examples/indexgen',
        help='The directory that the files/folders are located in. By'
        ' default, it is set to the "indexgen" directory.')
    parser.add_argument(
        '--file-name', default='indexgen.html',
        help='The name of the HTML file to be generated/updated. Should'
        ' contain the ".html" extension; default value is "indexgen.html".')
    args = parser.parse_args()

    generate_file()