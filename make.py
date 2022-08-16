#!/usr/bin/env python
import os
import os.path as op
import sys
import shutil
import webbrowser

from subprocess import call

THIS_DIR = op.dirname(op.abspath(__file__))
DOC_DIR = op.join(THIS_DIR, 'doc')
DIST_DIR = op.join(THIS_DIR, 'dist')
GENDIST_TOOL = op.join(THIS_DIR, 'tools', 'gendist.sh')


def clean():
    """Clean up all build & test artifacts, and generated documentation."""
    dirs = [op.join(DOC_DIR, '_build'),
            op.join(DOC_DIR, 'api'),
            DIST_DIR,
            op.join(THIS_DIR, '_build'),
            op.join(THIS_DIR, 'pyglet.egg-info'),
            op.join(THIS_DIR, '.pytest_cache'),
            op.join(THIS_DIR, '.mypy_cache')]
    files = [op.join(DOC_DIR, 'internal', 'build.rst')]
    for d in dirs:
        print('   Removing:', d)
        shutil.rmtree(d, ignore_errors=True)
    for f in files:
        print('   Removing:', f)
        try:
            os.remove(f)
        except OSError:
            pass


def docs():
    """Generate documentation"""
    make_bin = 'make.exe' if sys.platform == 'win32' else 'make'

    html_dir = op.join(DOC_DIR, '_build', 'html')
    if not op.exists(html_dir):
        os.makedirs(op.join(DOC_DIR, '_build', 'html'))
    call([make_bin, 'html'], cwd=DOC_DIR)
    if '--open' in sys.argv:
        webbrowser.open('file://' + op.abspath(DOC_DIR) + '/_build/html/index.html')


def dist():
    """Create all files to distribute Pyglet"""
    docs()
    call(GENDIST_TOOL)


def _print_usage():
    print('Usage:', op.basename(sys.argv[0]), '<command>')
    print('  where commands are:', ', '.join(avail_cmds))
    print()
    for name, cmd in avail_cmds.items():
        print(name, '\t', cmd.__doc__)


if __name__ == '__main__':
    avail_cmds = dict(clean=clean, dist=dist, docs=docs)
    try:
        command = avail_cmds[sys.argv[1]]
    except IndexError:
        # Invalid number of arguments, just print help
        _print_usage()
    except KeyError:
        print('Unknown command:', sys.argv[1])
        print()
        _print_usage()
    else:
        command()
