# 2. Create build/pyglet.wxs from pyglet.wxs, add all file components
# 3. Run candle and light on build/pyglet.wxs to generate
#    ../../dist/pyglet.msi

import os
import re
import shutil
import subprocess
from uuid import uuid1
from xml.dom.minidom import parse

exclude_packages = ['ext']

ids = set()
def id(name):
    num = 1
    id = name
    while id in ids:
        num += 1
        id = '%s%d' % (name, num)
    ids.add(id)
    return id

shortnames = set()
def shortname(name, ext):
    num = 1
    shortname = '%s.%s' % (name[:8], ext)
    while shortname in shortnames:
        num += 1
        shortname = '%s%02d.%s' % (name[:6], num, ext)
    shortnames.add(shortname)
    return shortname

def node(doc, node_name, **kwargs):
    node = doc.createElement(node_name)
    for key, value in kwargs.items():
        node.setAttribute(key, value)
    return node

def add_package(name, src_dir, doc, dest_node):
    if name in exclude_packages:
        return

    src_path = os.path.join(src_dir, name)

    directory = node(doc, 'Directory',
        Id=id('%sDir' % name),
        Name='%s.dir' % name[:8],
        LongName=name)
    dest_node.appendChild(doc.createTextNode('\n\n'))
    dest_node.appendChild(directory)
    dest_node.appendChild(doc.createTextNode('\n\n'))
    directory.appendChild(doc.createTextNode('\n'))

    for filename in os.listdir(src_path):
        file_path = os.path.join(src_path, filename)
        if os.path.isdir(file_path):
            if os.path.exists(os.path.join(file_path, '__init__.py')):
                add_package(filename, src_path, doc, directory)
        elif filename.endswith('.py'):
            add_module(filename, src_path, doc, directory)

components = []
def component_id(name):
    component = id(name)
    components.append(component)
    return component

guid_seq = 0
def guid():
    global guid_seq
    guid_seq += 1
    return uuid1(clock_seq=guid_seq).hex.upper()

def add_module(name, src_dir, doc, dest_node):
    src_path = os.path.join(src_dir, name)
    basefile = os.path.splitext(name)[0]

    component = node(doc, 'Component',
        Id= component_id('%sComponent' % basefile),
        Guid=guid())

    component.appendChild(
        node(doc, 'File',
             Id=id('%sPy' % basefile),
             Name=shortname(basefile, 'py'),
             LongName=name,
             DiskId='1',
             Source=src_path))
    component.appendChild(
        node(doc, 'RemoveFile',
             Id=id('%sPyc' % basefile),
             Name=shortname(basefile, 'pyc'),
             LongName='%s.pyc' % basefile,
             On='uninstall'))
    component.appendChild(
        node(doc, 'RemoveFile',
             Id=id('%sPyo' % basefile),
             Name=shortname(basefile, 'pyo'),
             LongName='%s.pyo' % basefile,
             On='uninstall'))
    dest_node.appendChild(component)

    # Some readability
    dest_node.appendChild(doc.createTextNode('\n'))

def call(cmd):
    print cmd
    return subprocess.call(cmd, shell=True)

if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    root_dir = os.path.join(script_dir, '../..')
    dist_dir = os.path.join(root_dir, 'dist')
    try:
        os.makedirs(dist_dir)
    except OSError:
        pass

    # Determine release version from setup.py
    version_re = re.compile("VERSION = '([^']*)'")
    for line in open(os.path.join(root_dir, 'setup.py')):
        match = version_re.match(line)
        if match:
            version = match.groups()[0]
    print 'Writing pyglet.wxs'

    # Open template wxs
    wxs = parse(os.path.join(script_dir, 'pyglet.in.wxs'))
    
    # Find site-packages Directory element
    for elem in wxs.getElementsByTagName('Directory'):
        if elem.getAttribute('LongName') == 'site-packages':
            site_packages = elem
            break
       
    # Find all modules and add components to wxs document
    add_package('pyglet', root_dir, wxs, site_packages)

    # Add all components to feature
    feature = wxs.getElementsByTagName('Feature')[0]
    for component in components:
        feature.appendChild(node(wxs, 'ComponentRef',
                                 Id=component))
        feature.appendChild(wxs.createTextNode('\n'))
    
    # Write wxs file
    wxs.writexml(open(os.path.join(script_dir, 'pyglet.wxs'), 'w'))
    
    # Compile
    call('candle -out %s %s' % (os.path.join(script_dir, 'pyglet.wixobj'),
                                os.path.join(script_dir, 'pyglet.wxs')))

    # Link
    call('light -out %s %s' %(os.path.join(dist_dir, 'pyglet-%s.msi' % version),
                               os.path.join(script_dir, 'pyglet.wixobj')))
