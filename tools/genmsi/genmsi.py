# 2. Create build/pyglet.wxs from pyglet.wxs, add all file components
# 3. Run candle and light on build/pyglet.wxs to generate
#    ../../dist/pyglet.msi

import os
import re
import shutil
import subprocess
from uuid import uuid1
from xml.dom.minidom import parse

import pkg_resources

class PythonVersion(object):
    def __init__(self, version, key_root, display_version):
        self.version = version
        self.display_version = display_version
        self.id = 'PY' + version.replace('.', '') + key_root
        self.key_root = key_root
        self.key = r'SOFTWARE\Python\PythonCore\%s\InstallPath' % version
        self.dir_prop = 'PYTHONHOME%s' % self.id
        self.exe_prop = 'PYTHONEXE%s' % self.id
        self.components = []
PYTHON_VERSIONS = (
    PythonVersion('2.4', 'HKLM', 'Python 2.4'),
    PythonVersion('2.5', 'HKLM', 'Python 2.5'),
    PythonVersion('2.6', 'HKLM', 'Python 2.6'),
    PythonVersion('2.4', 'HKCU', 'Python 2.4 (current user only)'),
    PythonVersion('2.5', 'HKCU', 'Python 2.5 (current user only)'),
    PythonVersion('2.6', 'HKCU', 'Python 2.6 (current user only)'),
)
MISSING_PYTHON_MESSAGE = 'pyglet requires Python 2.4 or later.  The ' \
                         'installation will be aborted.'

exclude_packages = []

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

def add_package(name, src_dir, doc, dest_node, pyver):
    if name in exclude_packages:
        return

    src_path = os.path.join(src_dir, name)

    directory = node(doc, 'Directory',
        Id=id('%sDir' % name),
        Name=name)
    dest_node.appendChild(doc.createTextNode('\n\n'))
    dest_node.appendChild(directory)
    dest_node.appendChild(doc.createTextNode('\n\n'))
    directory.appendChild(doc.createTextNode('\n'))

    for filename in os.listdir(src_path):
        file_path = os.path.join(src_path, filename)
        if os.path.isdir(file_path):
            if os.path.exists(os.path.join(file_path, '__init__.py')):
                add_package(filename, src_path, doc, directory, pyver)
        elif filename.endswith('.py'):
            add_module(filename, src_path, doc, directory, pyver)

def component_id(name, pyver):
    component = id(name)
    pyver.components.append(component)
    return component

guid_seq = 0
def guid():
    global guid_seq
    guid_seq += 1
    return uuid1(clock_seq=guid_seq).hex.upper()

def add_module(name, src_dir, doc, dest_node, pyver):
    src_path = os.path.join(src_dir, name)
    basefile = os.path.splitext(name)[0]

    component = node(doc, 'Component',
        Id= component_id('%sComponent' % basefile, pyver),
        Guid=guid())

    component.appendChild(
        node(doc, 'File',
             Id=id('%sPy' % basefile),
             Name=name,
             DiskId='1',
             Source=src_path))
    component.appendChild(
        node(doc, 'RemoveFile',
             Id=id('%sPyc' % basefile),
             Name='%s.pyc' % basefile,
             On='uninstall'))
    component.appendChild(
        node(doc, 'RemoveFile',
             Id=id('%sPyo' % basefile),
             Name='%s.pyo' % basefile,
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

    # Copy current avbin into res
    shutil.copyfile('c:/windows/system32/avbin.dll', 
                    os.path.join(script_dir, 'res', 'avbin.dll'))

    # Determine release version from setup.py
    version_re = re.compile("VERSION = '([^']*)'")
    for line in open(os.path.join(root_dir, 'setup.py')):
        match = version_re.match(line)
        if match:
            version = match.groups()[0]

    # Create a Windows-friendly dotted number for the version
    # Version string must not have any letters, so use:
    #   alpha = x.x.x.(0 + alpha num)
    #   beta = x.x.x.(16 + beta num)
    #   rc = x.x.x.(32 + rc num)
    #   release = x.x.x.128 -->
    parts = list(pkg_resources.parse_version(version))
    major = int(parts.pop(0))
    minor = patch = tagnum = 0
    if parts[0][0] != '*':
        minor = int(parts.pop(0))
    if parts[0][0] != '*':
        patch = int(parts.pop(0))
    tag = parts.pop(0)
    if tag == '*alpha':
        base = 0
    elif tag == '*beta':
        base = 16
    elif tag == '*rc':
        base = 32
    elif tag == '*final':
        base = 128
    else:
        assert False, 'Unrecognised version tag "%s"' % tag
    if parts and parts[0][0] != '*':
        tagnum = int(parts.pop(0))
    assert not parts or parts[0] == '*final'

    version_windows = '%d.%d.%d.%d' % (major, minor, patch, base + tagnum)
    print 'Version %s is Windows version %s' % (version, version_windows)
    
    print 'Writing pyglet.wxs'

    # Open template wxs and find Product element
    wxs = parse(os.path.join(script_dir, 'pyglet.in.wxs'))
    Product = wxs.getElementsByTagName('Product')[0]
    Product.setAttribute('Version', version_windows)

    # Add Python discovery
    for pyver in PYTHON_VERSIONS:
        Property = node(wxs, 'Property', 
                        Id=pyver.dir_prop)
        Property.appendChild(
            node(wxs, 'RegistrySearch',
                 Id='%sRegSearch' % pyver.dir_prop,
                 Root=pyver.key_root,
                 Key=pyver.key,
                 Type='directory'))
        Product.appendChild(Property) 
    
    # Add install conditional on at least one Python version present.
    Condition = node(wxs, 'Condition',
                     Message=MISSING_PYTHON_MESSAGE)
    Condition.appendChild(wxs.createTextNode(
        ' or '.join([pyver.dir_prop for pyver in PYTHON_VERSIONS])))
    Product.appendChild(Condition)

    
    # Get TARGETDIR Directory element
    for elem in wxs.getElementsByTagName('Directory'):
        if elem.getAttribute('Id') == 'TARGETDIR':
            target_dir = elem
            break
       
    # Create entire set of components for each python version (WiX 3 will
    # ensure only one copy of the source file is in the archive)
    for pyver in PYTHON_VERSIONS:
        python_home = node(wxs, 'Directory', 
                           Id=pyver.dir_prop)
        target_dir.appendChild(python_home)

        lib_dir = node(wxs, 'Directory',
                       Id='%sLibDir' % pyver.dir_prop,
                       Name='Lib')
        python_home.appendChild(lib_dir)

        site_packages = node(wxs, 'Directory',
                             Id='%sSitePackages' % pyver.dir_prop,
                             Name='site-packages')
        lib_dir.appendChild(site_packages)
                             
        add_package('pyglet', root_dir, wxs, site_packages, pyver)

    # Add all components to features
    RuntimeFeature = wxs.getElementsByTagName('Feature')[0]
    for pyver in PYTHON_VERSIONS:
        feature = node(wxs, 'Feature',
                       Id='RuntimeFeature%s' % pyver.id,
                       Title='pyglet runtime for %s' % pyver.display_version,
                       Level='1',
                       AllowAdvertise='no')
        condition = node(wxs, 'Condition',
                         Level='0')
        condition.appendChild(wxs.createTextNode('NOT ' + pyver.dir_prop))
        feature.appendChild(condition)
        for component in pyver.components:
            feature.appendChild(node(wxs, 'ComponentRef',
                                     Id=component))
            feature.appendChild(wxs.createTextNode('\n'))
        RuntimeFeature.appendChild(feature)

    # Add byte compilation custom actions
    last_action = 'InstallFinalize'
    InstallExecuteSequence = \
        wxs.getElementsByTagName('InstallExecuteSequence')[0]
    UI = wxs.getElementsByTagName('UI')[0]
    for pyver in PYTHON_VERSIONS:
        # Actions are conditional on the feature being installed
        def cond(node):
            node.appendChild(wxs.createTextNode(
                '(&RuntimeFeature%s=3) AND NOT(!RuntimeFeature%s=3)' % (
                    pyver.id, pyver.id)))
            return node
        
        # Define the actions
        Product.appendChild(node(wxs, 'CustomAction',
          Id='SetPythonExe%s' % pyver.id,
          Property=pyver.exe_prop,
          Value=r'[%s]\pythonw.exe' % pyver.dir_prop))
        Product.appendChild(node(wxs, 'CustomAction',
          Id='ByteCompile%s' % pyver.id,
          Property=pyver.exe_prop,
          ExeCommand=r'-c "import compileall; compileall.compile_dir(\"[%s]\Lib\site-packages\pyglet\", force=1)"' % pyver.dir_prop,
          Return='ignore'))
        Product.appendChild(node(wxs, 'CustomAction',
          Id='ByteOptimize%s' % pyver.id,
          Property=pyver.exe_prop,
          ExeCommand=r'-OO -c "import compileall; compileall.compile_dir(\"[%s]\Lib\site-packages\pyglet\", force=1)"' % pyver.dir_prop,
          Return='ignore'))

        # Schedule execution of these actions
        InstallExecuteSequence.appendChild(cond(
            node(wxs, 'Custom',
                 Action='SetPythonExe%s' % pyver.id,
                 After=last_action)))
        InstallExecuteSequence.appendChild(cond(
            node(wxs, 'Custom',
                 Action='ByteCompile%s' % pyver.id,
                 After='SetPythonExe%s' % pyver.id)))
        InstallExecuteSequence.appendChild(cond(
            node(wxs, 'Custom',
                 Action='ByteOptimize%s' % pyver.id,
                 After='ByteCompile%s' % pyver.id)))
        last_action = 'ByteOptimize%s' % pyver.id
        
        # Set progress text for the actions
        progress = node(wxs, 'ProgressText',
                        Action='ByteCompile%s' % pyver.id)
        progress.appendChild(wxs.createTextNode(
            'Byte-compiling modules for Python %s' % pyver.version))
        UI.appendChild(progress)
        progress = node(wxs, 'ProgressText',
                        Action='ByteOptimize%s' % pyver.id)
        progress.appendChild(wxs.createTextNode(
            'Byte-optimizing modules for Python %s' % pyver.version))
        UI.appendChild(progress)
    
    # Write wxs file
    wxs.writexml(open(os.path.join(script_dir, 'pyglet.wxs'), 'w'))
    
    # Compile
    call('candle -out %s %s' % (os.path.join(script_dir, 'pyglet.wixobj'),
                                os.path.join(script_dir, 'pyglet.wxs')))

    # Link
    call('light -sval -out %s %s' % \
        (os.path.join(dist_dir, 'pyglet-%s.msi' % version),
         os.path.join(script_dir, 'pyglet.wixobj')))
