#!/usr/bin/python
# $Id:$

'''Rewrite the license header of source files.

Usage:
    license.py file.py file.py dir/ dir/ ...
'''

import optparse
import os
import sys

license = '''# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.'''

marker = '# ' + '-' * 76

license_lines = [marker] + license.split('\n') + [marker]

def update_license(filename):
    '''Open a Python source file and update the license header, writing
    it back in place.'''
    lines = [l.strip('\r\n') for l in open(filename).readlines()]
    if marker in lines:
        # Update existing license
        try:
            marker1 = lines.index(marker)
            marker2 = lines.index(marker, marker1 + 1)
            if marker in lines[marker2 + 1:]:
                raise ValueError() # too many markers
            lines = (lines[:marker1] + 
                     license_lines + 
                     lines[marker2 + 1:])
        except ValueError:
            print >> sys.stderr, "Can't update license in %s" % filename
    else:
        # Add license to unmarked file
        # Skip over #! if present
        if not lines:
            pass # Skip empty files
        elif lines[0].startswith('#!'):
            lines = lines[:1] + license_lines + lines[1:]
        else:
            lines = license_lines + lines
    open(filename, 'wb').write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('--exclude', action='append', default=[])
    options, args = op.parse_args()
    
    if len(args) < 1:
        print >> sys.stderr, __doc__
        sys.exit(0)

    for path in args:
        if os.path.isdir(path):
            for root, dirnames, filenames in os.walk(path):
                for dirname in dirnames:
                    if dirname in options.exclude:
                        dirnames.remove(dirname)
                for filename in filenames:
                    if (filename.endswith('.py') and 
                        filename not in options.exclude):
                        update_license(os.path.join(root, filename))
        else:
            update_license(path)
