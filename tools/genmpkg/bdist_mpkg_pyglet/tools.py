import os
import sys
from itertools import chain
from distutils.util import spawn
from distutils.version import StrictVersion, LooseVersion
from distutils.dir_util import mkpath
import distutils.core

try:
    set
except NameError:
    from sets import Set as set

def Version(s):
    try:
        return StrictVersion(s)
    except ValueError:
        return LooseVersion(s)

def run_setup(*args, **kwargs):
    """
    Re-entrant version of distutils.core.run_setup()
    """
    PRESERVE = '_setup_stop_after', '_setup_distribution'
    d = {}
    for k in PRESERVE:
        try:
            d[k] = getattr(distutils.core, k)
        except AttributeError:
            pass
    try:
        return distutils.core.run_setup(*args, **kwargs)
    finally:
        for k,v in d.iteritems():
            setattr(distutils.core, k, v)

def adminperms(src, verbose=0, dry_run=0):
    try:
        # Awful unavoidable quirk: package must be built as root.
        spawn(['/usr/sbin/chown', '-R', 'root', src])
        spawn(['/usr/bin/chgrp', '-R', 'admin', src])
        spawn(['/bin/chmod', '-R', 'u=rwX,g=rwX,o=rX', src])
    except:
        raise RuntimeError('Cannot chown/chgrp/chmod.  Are you running sudo?')
    return True

def mkbom(src, pkgdir, verbose=0, dry_run=0, TOOL='/usr/bin/mkbom'):
    """
    Create a bill-of-materials (BOM) for the given src directory and store it
    to the given pkg directory
    """
    dest = os.path.join(pkgdir, 'Contents', 'Archive.bom')
    mkpath(os.path.dirname(dest), verbose=verbose, dry_run=dry_run)
    spawn([TOOL, src, dest], verbose=verbose, dry_run=dry_run)

def pax(src, pkgdir, verbose=0, dry_run=0, TOOL='/bin/pax'):
    """
    Create a pax gzipped cpio archive of the given src directory and store it
    to the given pkg directory

    returns size of archive
    """
    dest = os.path.realpath(os.path.join(pkgdir, 'Contents', 'Archive.pax.gz'))
    mkpath(os.path.dirname(dest), verbose=verbose, dry_run=dry_run)
    pwd = os.path.realpath(os.getcwd())
    os.chdir(src)
    try:
        spawn([TOOL, '-w', '-f', dest, '-x', 'cpio', '-z', '.'])
    finally:
        os.chdir(pwd)
    return os.stat(dest).st_size

def unicode_path(path, encoding=sys.getfilesystemencoding()):
    if isinstance(path, unicode):
        return path
    return unicode(path, encoding)

def walk_files(path):
    for root, dirs, files in os.walk(path):
        for fn in files:
            yield os.path.join(root, fn)

def get_gid(name, _cache={}):
    if not _cache:
        for line in os.popen('/usr/bin/nidump group .'):
            fields = line.split(':')
            if len(fields) >= 3:
                _cache[fields[0]] = int(fields[2])
    try:
        return _cache[name]
    except KeyError:
        raise ValueError('group %s not found' % (name,))

def find_root(path, base='/'):
    """
    Return the list of files, the archive directory, and the destination path
    """
    files = list(walk_files(path))
    common = os.path.dirname(os.path.commonprefix(files))
    prefix = os.path.join(base, common[len(os.path.join(path, '')):])
    #while not os.path.exists(prefix):
    #    common = os.path.dirname(common)
    #    prefix = os.path.dirname(prefix)
    prefix = os.path.realpath(prefix)
    return files, common, prefix

def admin_writable(path):
    gid = get_gid('admin')
    while not os.path.exists(path):
        path = os.path.dirname(path)
    s = os.stat(path)
    mode = s.st_mode
    return (mode & 00002) or (s.st_gid == gid and mode & 00020)

def reduce_size(files):
    return sum([os.stat(fn).st_size for fn in files])

def sw_vers(_cache=[]):
    if not _cache:
        info = os.popen('/usr/bin/sw_vers').read().splitlines()
        for line in info:
            key, value = line.split(None, 1)
            if key == 'ProductVersion:':
                _cache.append(Version(value.strip()))
                break
        else:
            raise ValueError("sw_vers not behaving correctly")
    return _cache[0]

def is_framework_python():
    return os.path.dirname(os.path.dirname(sys.prefix)).endswith('.framework')
