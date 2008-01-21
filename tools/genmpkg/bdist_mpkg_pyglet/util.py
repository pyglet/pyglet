import os, sys
try:
    set
except NameError:
    from sets import Set as set

def fsencoding(s, encoding=sys.getfilesystemencoding()):
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s

SCMDIRS = ['CVS', '.svn']
def skipscm(ofn):
    ofn = fsencoding(ofn)
    fn = os.path.basename(ofn)
    if fn in SCMDIRS:
        return False
    return True

def skipfunc(junk=(), junk_exts=(), chain=()):
    junk = set(junk)
    junk_exts = set(junk_exts)
    chain = tuple(chain)
    def _skipfunc(fn):
        if os.path.basename(fn) in junk:
            return False
        elif os.path.splitext(fn)[1] in junk_exts:
            return False
        for func in chain:
            if not func(fn):
                return False
        else:
            return True
    return _skipfunc

JUNK = ['.DS_Store', '.gdb_history', 'build', 'dist'] + SCMDIRS
JUNK_EXTS = ['.pbxuser', '.pyc', '.pyo', '.swp']
skipjunk = skipfunc(JUNK, JUNK_EXTS)

def copy_tree(src, dst,
        preserve_mode=1,
        preserve_times=1,
        preserve_symlinks=0,
        update=0,
        verbose=0,
        dry_run=0,
        condition=None):

    """
    Copy an entire directory tree 'src' to a new location 'dst'.  Both
    'src' and 'dst' must be directory names.  If 'src' is not a
    directory, raise DistutilsFileError.  If 'dst' does not exist, it is
    created with 'mkpath()'.  The end result of the copy is that every
    file in 'src' is copied to 'dst', and directories under 'src' are
    recursively copied to 'dst'.  Return the list of files that were
    copied or might have been copied, using their output name.  The
    return value is unaffected by 'update' or 'dry_run': it is simply
    the list of all files under 'src', with the names changed to be
    under 'dst'.

    'preserve_mode' and 'preserve_times' are the same as for
    'copy_file'; note that they only apply to regular files, not to
    directories.  If 'preserve_symlinks' is true, symlinks will be
    copied as symlinks (on platforms that support them!); otherwise
    (the default), the destination of the symlink will be copied.
    'update' and 'verbose' are the same as for 'copy_file'.
    """


    from distutils.dir_util import mkpath
    from distutils.file_util import copy_file
    from distutils.dep_util import newer
    from distutils.errors import DistutilsFileError
    from distutils import log

    src = fsencoding(src)
    dst = fsencoding(dst)

    if condition is None:
        condition = skipjunk

    if not dry_run and not os.path.isdir(src):
        raise DistutilsFileError(
            "cannot copy tree '%s': not a directory" % src)
    try:
        names = os.listdir(src)
    except os.error, (errno, errstr):
        if dry_run:
            names = []
        else:
            raise DistutilsFileError("error listing files in '%s': %s" % (
                src, errstr))

    if not dry_run:
        mkpath(dst)

    outputs = []

    for n in names:
        src_name = os.path.join(src, n)
        dst_name = os.path.join(dst, n)
        if (condition is not None) and (not condition(src_name)):
            continue

        if preserve_symlinks and os.path.islink(src_name):
            link_dest = os.readlink(src_name)
            log.info("linking %s -> %s", dst_name, link_dest)
            if not dry_run:
                if update and not newer(src, dst_name):
                    pass
                else:
                    if os.path.islink(dst_name):
                        os.remove(dst_name)
                    os.symlink(link_dest, dst_name)
            outputs.append(dst_name)

        elif os.path.isdir(src_name):
            outputs.extend(
                copy_tree(src_name, dst_name, preserve_mode,
                          preserve_times, preserve_symlinks, update,
                          dry_run=dry_run, condition=condition))
        else:
            copy_file(src_name, dst_name, preserve_mode,
                      preserve_times, update, dry_run=dry_run)
            outputs.append(dst_name)

    return outputs
