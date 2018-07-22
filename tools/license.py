#!/usr/bin/python
# $Id:$

"""Rewrite the license header of source files.

Usage:
    license.py file.py file.py dir/ dir/ ...
"""

import os
import sys
import datetime
import optparse


license_str = """# pyglet
# Copyright (c) 2006-{0} Alex Holkner
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
# POSSIBILITY OF SUCH DAMAGE.""".format(datetime.datetime.now().year)

marker = '# ' + '-' * 76

license_lines = [marker] + license_str.split('\n') + [marker]


def update_license(file_name):
    """Open a Python source file and update the license header in place."""
    lines = [l.strip('\r\n') for l in open(file_name).readlines()]
    if marker in lines:
        # Update existing license
        print("Updating license in: '{0}'".format(file_name))
        try:
            marker1 = lines.index(marker)
            marker2 = lines.index(marker, marker1 + 1)
            if marker in lines[marker2 + 1:]:
                raise ValueError()  # too many markers
            lines = (lines[:marker1] +
                     license_lines +
                     lines[marker2 + 1:])
        except ValueError:
            print("Can't update license in %s" % file_name, file=sys.stderr)

    else:
        # Add license to unmarked file. Skip over #! if present.
        print("Adding license to: '{0}'".format(file_name))
        if not lines:
            pass    # Skip empty files
        elif lines[0].startswith('#!'):
            lines = lines[:1] + license_lines + lines[1:]
        else:
            lines = license_lines + lines

    open(file_name, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('--exclude', action='append', default=[])
    options, args = op.parse_args()
    
    if len(args) < 1:
        print(__doc__, file=sys.stderr)
        sys.exit(0)

    for path in args:
        if os.path.isdir(path):
            for root, dirnames, filenames in os.walk(path):
                for dirname in dirnames:
                    if dirname in options.exclude:
                        dirnames.remove(dirname)
                for filename in filenames:
                    if filename.endswith('.py') and filename not in options.exclude:
                        update_license(os.path.join(root, filename))
        else:
            update_license(path)
