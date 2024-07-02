#!/usr/bin/env python
import os
import os.path as op
import sys
import shutil
import webbrowser

THIS_DIR = op.dirname(op.abspath(__file__))
DOC_DIR = op.join(THIS_DIR, 'doc')
DIST_DIR = op.join(THIS_DIR, 'dist')


def clean():
    """Clean up all build & test artifacts, and generated documentation."""
    dirs = [op.join(DOC_DIR, '_build'),
            op.join(DOC_DIR, 'api'),
            DIST_DIR,
            op.join(THIS_DIR, '_build'),
            op.join(THIS_DIR, 'pyglet.egg-info'),
            op.join(THIS_DIR, '.pytest_cache'),
            op.join(THIS_DIR, '.mypy_cache'),
            op.join(THIS_DIR, '.ruff_cache')]

    files = [op.join(DOC_DIR, 'internal', 'build.rst')]

    for d in dirs:
        if not op.exists(d):
            continue
        shutil.rmtree(d, ignore_errors=True)
        print(f"   Removed: {d}")

    for f in files:
        if not op.exists(f):
            continue
        try:
            os.remove(f)
            print(f"   Removed: {f}")
        except OSError:
            print(f"   Failed to remove: {f}")


def docs():
    """Generate documentation"""
    try:
        import sphinx.cmd.build
    except ImportError:
        print("The 'sphinx' package, and several dependencies are required for building documentation. "
              "See 'doc/requirements.txt' for dependencies, and 'doc/README.md' for more information.")
        exit(1)

    # Ensure the build director exists:
    html_dir = op.join(DOC_DIR, '_build', 'html')
    os.makedirs(op.join(DOC_DIR, '_build', 'html'), exist_ok=True)

    # Should be similar to `sphinx-build` on the CLI:
    return_code = sphinx.cmd.build.build_main([DOC_DIR, html_dir])
    if '--open' in sys.argv:
        if return_code == 0:
            webbrowser.open('file://' + op.abspath(DOC_DIR) + '/_build/html/index.html')
        else:
            print("Skipping --open preview due doc build failure")

    exit(return_code)


def dist():
    """Create files to distribute pyglet"""
    try:
        import flit
    except ImportError:
        print("The 'flit' package is required for building pyglet.")
        exit(1)

    flit.main(['build'])


def _print_usage():
    print('Usage:', op.basename(sys.argv[0]), '<command>')
    print('  where commands are:', ', '.join(avail_cmds), "\n")
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
        print(f"Unknown command: {sys.argv[1]}\n")
        _print_usage()
    else:
        command()
