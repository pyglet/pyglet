#!/usr/bin/env python

'''Upload dist/ files to code.google.com.  For Alex only :-)
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import re
import sys

base = os.path.dirname(__file__)
root = os.path.join(base, '../..')
dist = os.path.join(root, 'dist')

sys.path.insert(0, root)
import pyglet

import googlecode_upload

if __name__ == '__main__':
    version = 'pyglet-%s' % pyglet.version
    print 'Preparing to upload %s' % version

    password = open(os.path.expanduser('~/.googlecode-passwd')).read().strip()

    descriptions = {}
    for line in open(os.path.join(base, 'descriptions.txt')):
        suffix, description = line.split(' ', 1)
        descriptions[suffix] = description.strip()

    files = {}
    version_pattern = re.compile('%s[.-].*' % version)
    for filename in os.listdir(dist):
        if version_pattern.match(filename):
            description = descriptions.get(filename[len(version):])
            if not description:
                print 'No description for %s' % filename
                sys.exit(1)
            description = '%s %s' % (pyglet.version, description)
            
            labels = []
            if filename.endswith('.tar.gz') or filename.endswith('.zip') and\
               'docs' not in filename:
                labels.append('Type-Source')
            elif filename.endswith('.msi'):
                labels.append('OpSys-Windows')
            elif filename.endswith('.dmg'):
                labels.append('OpSys-OSX')
            # Don't feature 1.1 until release time
            #if not filename.endswith('.egg'):
            #    labels.append('Featured')
            files[filename] = description, labels

            print filename
            print '   %s' % description
            print '   %s' % ', '.join(labels)

    print 'Ok to upload? [type "y"]'
    if raw_input().strip() != 'y':
        print 'Aborted.'
        sys.exit(1)

    for filename, (description, labels) in files.items():
        status, reason, url = googlecode_upload.upload(
            os.path.join(dist, filename),
            'pyglet',
            'Alex.Holkner',
            password,
            description,
            labels)
        if url:
            print 'OK: %s' % url
        else:
            print 'Error: %s (%s)' % (reason, status)

    print 'Done!'
