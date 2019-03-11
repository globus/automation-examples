#!/usr/bin/env python

"""
Generates the an Markdown file that lists all of the files
in a directory.
"""

from __future__ import print_function
import os
import sys
import argparse
import shutil

md_header = ''.join([
'''
# Index of {directory}
'''
])

markdown_section = '''
[{name}]({path})
'''

get_input = getattr(__builtins__, 'raw_input', input)

def generate_file():
    """
    Goes through the directory and generates the Markdown file.
    """
    print("\nGenerating the Markdown file")
    md = md_header.format(directory=args.directory)
    cwd = os.getcwd()
    path = os.path.normpath(os.path.join(cwd, 'docs/examples', args.directory))
    for root, dirs, files in os.walk(path):
        for name in files:
            print(name)
            file_path = join_path_names('./examples/', args.directory, name)
            md += markdown_section.format(name=name, path=file_path)

    file_path = os.path.join('docs/', args.file_name)
    with open(file_path, 'w') as index_file:
        index_file.write(md)

def join_path_names(path_one, path_two, *argv):
    full_path = os.path.normpath(path_one + '/' + path_two)
    for arg in argv:
        full_path = os.path.normpath(full_path + '/' + arg)
        
    return full_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generates the an Markdown file that lists all of'
        ' the files in a directory.'
    )
    parser.add_argument(
        '--directory', default='indexgen',
        help='The directory that the files/folders are located in. By'
        ' default, it is set to the "indexgen" directory.')
    parser.add_argument(
        '--file-name', default='index.md',
        help='The name of the Markdown file to be generated/updated. Should'
        ' contain the ".md" extension; default value is "indexgen.md".')
    args = parser.parse_args()

    generate_file()