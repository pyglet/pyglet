#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import shutil
import sys

# Bump pyglet/__init__.py version as well.
VERSION = '1.0alpha1'

long_description = '''pyglet provides an object-oriented programming
interface for developing games and other visually-rich applications
for Windows, Mac OS X and Linux.  Some of the features of pyglet are:

* No external dependencies or installation requirements. Users of your
  application need only install Python to experience a first-class
  application featuring 3D graphics, sound and video. pyglet is written
  in pure Python, so no dangerous binaries are required.
* Take advantage of multiple windows and multi-monitor desktops. pyglet
  allows you to use as many windows as you need, and is fully aware of
  multi-monitor setups for use with fullscreen games.
* Load images, sound, music and video in almost any format. pyglet can
  use any installed codecs to read media files. On Windows, Linux and
  Mac OS X this means you get access to PNG, JPEG, MP3, MPEG-1 and many
  other file types even with a clean operating system install.

'''

setup_info = dict(
    # Metadata
    name='pyglet',
    version=VERSION,
    author='Alex Holkner',
    author_email='Alex.Holkner@gmail.com',
    url='http://www.pyglet.org/',
    description='Cross-platform windowing and multimedia library',
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Mac OS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: Developers',
        'License :: OS Approved :: BSD License',
        'Operating System :: MacOS :: Mac OS X',
        'Operating System :: Microsoft :: Windows', # XP
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # Package info
    packages=[
        'pyglet', 
        'pyglet.gl', 
        'pyglet.font', 
        'pyglet.image', 
        'pyglet.image.codecs',
        'pyglet.media', 
        'pyglet.window', 
        'pyglet.window.carbon',
        'pyglet.window.win32', 
        'pyglet.window.xlib',
    ],
)

setuptools_info = dict(
    zip_safe=True,
)

if 'bdist_egg' in sys.argv:
    from setuptools import setup
    _have_setuptools = True

    # Don't walk SVN tree for default manifest
    from setuptools.command import egg_info
    from setuptools.command import sdist
    egg_info.walk_revctrl = lambda: []
    sdist.walk_revctrl = lambda: []

    # Insert additional command-line arguments into install_lib when
    # bdist_egg calls it, to compile byte-code with optimizations.
    # This is a dirty hack.
    from setuptools.command import bdist_egg
    old_call_command = bdist_egg.bdist_egg.call_command
    def call_command(self, *args, **kwargs):
        if args[0] == 'install_lib':
            kwargs['optimize'] = 2
            kwargs['compile'] = False
        cmd = old_call_command(self, *args, **kwargs)
        return cmd
    bdist_egg.bdist_egg.call_command = call_command

elif 'bdist_mpkg' in sys.argv:
    from setuptools import setup
    _have_setuptools = True
    
    # Allow PDF background image
    from bdist_mpkg import pkg
    pkg.IMAGE_EXTS = ('.pdf',)

    # Fix background filename by overriding pkg.copy_doc
    old_copy_doc = pkg.copy_doc
    def copy_doc(path, name, *args, **kwargs):
        if name == 'Background':
            name = 'background'
        return old_copy_doc(path, name, *args, **kwargs)
    pkg.copy_doc = copy_doc

    # Check for ctypes if installing into Python 2.4
    from bdist_mpkg import plists
    def ctypes_requirement(pkgname, prefix):
        prefix = os.path.join(prefix, 'ctypes')
        title = '%s requires ctypes 1.0 or later to install with Python 2.4' \
           % pkgname
        kw = dict(
            LabelKey='ctypes',
            TitleKey=title,
            MessageKey=title,
        )

        return plists.path_requirement(prefix, **kw)

    # Subclass bdist_mpkg
    from bdist_mpkg import cmd_bdist_mpkg
    class pyglet_bdist_mpkg(cmd_bdist_mpkg.bdist_mpkg):
        # Don't include platform or python version in mpkg name (aesthetics)
        def finalize_package_data(self):
            cmd_bdist_mpkg.bdist_mpkg.finalize_package_data(self)
            self.metapackagename = '-'.join([self.get_name(),
                                             self.get_version()]) + '.mpkg'
            self.pseudoinstall_root = self.get_pseudoinstall_root()
            self.packagesdir = os.path.join(
                self.get_metapackage(),
                self.component_directory
            )

        def get_metapackage_info(self):
            info = dict(cmd_bdist_mpkg.bdist_mpkg.get_metapackage_info(self))
            info.update(dict(
                # Set background image alignment 
                IFPkgFlagBackgroundScaling='none',
                IFPkgFlagBackgroundAlignment='topleft',
                # Remove specific Python version requirement from metapackage,
                # is per-package now.
                IFRequirementDicts=[],
            ))
            return info

        # Override how packages are made.  purelib forces creation of a
        # separate package for each required python version, all symlinked to
        # the same Archive.bom.
        def make_scheme_package(self, scheme):
            assert scheme == 'purelib'
            files, common, prefix = self.get_scheme_root(scheme)

            # Hardcoded per-version prefix
            prefix_template = '/Library/Frameworks/Python.framework/Versions/'

            for pyver in ('2.4', '2.5'):
                python_prefix = (
                    '/Library/Frameworks/Python.framework/Versions/' +
                    pyver)
                scheme_prefix = (
                    python_prefix + 
                    '/lib/python%s/site-packages' % pyver)
                pkgname = '-'.join((self.get_name(), 'py' + pyver))
                pkgfile = pkgname + '.pkg'
                self.packages.append((pkgfile, self.get_scheme_status(scheme)))
                pkgdir = os.path.join(self.packagesdir, pkgfile)
                self.mkpath(pkgdir)
                version = self.get_scheme_version(scheme)

                requirements = [
                    plists.python_requirement(self.get_name(),
                        prefix=python_prefix,
                        version=pyver)]
                if pyver == '2.4':
                    requirements.append(ctypes_requirement(self.get_name(),
                        prefix=scheme_prefix))

                info = dict(self.get_scheme_info(scheme))
                info.update(dict(
                    IFRequirementDicts=requirements,
                    ))
                description = '%s for Python %s' % (self.get_name(), pyver)

                pkg.make_package(self,
                    pkgname, version,
                    files, common, scheme_prefix,
                    pkgdir,
                    info,
                    description,
                )

                # Move the archive up to the metapackage and symlink to it
                pkgfile = os.path.join(pkgdir, 'Contents/Archive.pax.gz')
                shutil.move(pkgfile, 
                            os.path.join(pkgdir, '../../Archive.pax.gz'))
                os.symlink('../../../Archive.pax.gz', pkgfile)

                pkgfile = os.path.join(pkgdir, 'Contents/Archive.bom')
                shutil.move(pkgfile, 
                            os.path.join(pkgdir, '../../Archive.bom'))
                os.symlink('../../../Archive.bom', pkgfile)

                self.scheme_hook(scheme, pkgname, version, files, common,
                    prefix, pkgdir)

        # Don't build to an absolute path, assume within site-packages (makes
        # it easier to symlink the same archive for all packages)
        def get_scheme_install_prefix(self, scheme):
            return scheme

        # Don't byte compile (waste of space, try to do it in postflight TODO).
        def byte_compile(self):
            pass

    setuptools_info.update(dict(
        cmdclass={'bdist_mpkg': pyglet_bdist_mpkg,}
    ))

else:
    from distutils.core import setup
    _have_setuptools = False



if _have_setuptools:
    # Additional dict values for setuptools
    setup_info.update(setuptools_info)

    install_requires = []
    if sys.version_info < (2, 5, 0):
        install_requires.append('ctypes')
    setup_info.update(dict(
        install_requires=install_requires,
    ))

setup(**setup_info)
