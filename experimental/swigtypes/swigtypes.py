#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import optparse
import os
import re
import subprocess
import sys

import parse

def create_swig_interface(header_filename, interface_filename, 
                          includes=(), module_name=None, defines=()):
    defines = list(defines)
    defines += [
        '_WCHAR_T=wchar_t',
        r'__attribute__\(x\)=',
        '__restrict=',
        '__const=',
        '__extension__=',
        '__signed__=signed',
    ]

    includes = ['-I' + include for include in includes]
    defines = ['-D' + define for define in defines]

    cflags = ' '.join(includes + defines)

    interface_file = open(interface_filename, 'w')
    skip_predefined_macros_re = re.compile('^#define __.*', flags=re.DOTALL)

    if module_name is None:
        module_name, _ = os.path.splitext(os.path.basename(header_filename))
    print >> interface_file, '%%module %s' % module_name 

    cmd = 'gcc %s -E -P -dD %s -o -' % (
        cflags, header_filename)
    print cmd
    gcc = subprocess.Popen(cmd, 
        stdout=subprocess.PIPE,
        shell=True)
    for line in gcc.stdout.readlines():
        if not skip_predefined_macros_re.match(line):
            interface_file.write(line)
    gcc.stdout.close()
    interface_file.close()

def create_swig_xml(interface_filename, xml_filename):
    cmd = 'swig -xml -xmllite -o %s %s' % (xml_filename, interface_filename)
    print cmd
    result = subprocess.call(cmd, shell=True)
    if result:
        sys.exit(result)

if __name__ == '__main__':
    usage = 'usage: %prog [options] <header.h>'
    op = optparse.OptionParser(usage=usage)
    op.add_option('-o', '--output')
    op.add_option('-i', '--interface-file')
    op.add_option('-x', '--xml-file')
    op.add_option('-I', dest='includes', action='append', default=[])
    op.add_option('-D', dest='defines', action='append', default=[])
    (options, args) = op.parse_args(sys.argv[1:])

    if len(args) < 1:
        print >> sys.stderr, 'No input file given'
        sys.exit(1)

    header_filename = args[0]
    module_name, _ = os.path.splitext(os.path.basename(header_filename))
    if options.interface_file is None:
        options.interface_file = module_name + '.i'
    if options.xml_file is None:
        options.xml_file = module_name + '.xml'
    if options.output is None:
        options.output = module_name + '.ffi'

    create_swig_interface(header_filename, options.interface_file, 
        includes=options.includes, defines=options.defines)
    create_swig_xml(options.interface_file, options.xml_file)
    parse.parse(options.xml_file, options.output)
    
