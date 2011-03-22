#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import shutil
import sys

# Bump pyglet/__init__.py version as well.
VERSION = '1.2dev'

long_description = '''pyglet provides an object-oriented programming
interface for developing games and other visually-rich applications
for Windows, Mac OS X and Linux.'''

setup_info = dict(
    # Metadata
    name='pyglet',
    version=VERSION,
    author='Alex Holkner',
    author_email='Alex.Holkner@gmail.com',
    url='http://www.pyglet.org/',
    download_url='http://www.pyglet.org/download.html',
    description='Cross-platform windowing and multimedia library',
    long_description=long_description,
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows', # XP
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # Package info
    packages=[
        'pyglet', 
        'pyglet.app',
        'pyglet.canvas',
        'pyglet.font', 
        'pyglet.gl', 
        'pyglet.graphics',
        'pyglet.image', 
        'pyglet.image.codecs',
        'pyglet.input',
        'pyglet.libs',
        'pyglet.libs.darwin',
        'pyglet.libs.win32',
        'pyglet.libs.x11',
        'pyglet.media', 
        'pyglet.media.drivers', 
        'pyglet.media.drivers.directsound', 
        'pyglet.media.drivers.openal', 
        'pyglet.media.drivers.pulse', 
        'pyglet.text',
        'pyglet.text.formats',
        'pyglet.window', 
        'pyglet.window.carbon',
        'pyglet.window.cocoa',
        'pyglet.window.win32', 
        'pyglet.window.xlib',
    ],
)

setuptools_info = dict(
    zip_safe=True,
)

if 'bdist_egg' in sys.argv or 'develop' in sys.argv:
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

    from bdist_mpkg_pyglet import plists, pkg, cmd_bdist_mpkg, tools
    
    # Check for ctypes if installing into Python 2.4
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

            # Make AVbin package
            pkgname = 'AVbin'
            pkgfile = pkgname + '.pkg'
            self.packages.append((pkgfile, self.get_scheme_status(scheme)))
            pkgdir = os.path.join(self.packagesdir, pkgfile)
            self.mkpath(pkgdir)
            version = self.get_scheme_version(scheme)
            info = dict(self.get_scheme_info(scheme))
            description = 'AVbin audio and video support (recommended)'
            files = list(tools.walk_files('build/avbin'))
            common = 'build/avbin'
            prefix = '/usr/local/lib'
            pkg.make_package(self,
                pkgname, version,
                files, common, prefix,
                pkgdir,
                info, description)

            # pyglet packages
            files, common, prefix = self.get_scheme_root(scheme)

            def add_package(python_dir, package_dir, 
                            pyver, pkgname, description):
                scheme_prefix = package_dir
                pkgfile = pkgname + '.pkg'
                self.packages.append((pkgfile, self.get_scheme_status(scheme)))
                pkgdir = os.path.join(self.packagesdir, pkgfile)
                self.mkpath(pkgdir)
                version = self.get_scheme_version(scheme)

                requirements = [
                    plists.python_requirement(self.get_name(),
                        prefix=python_dir,
                        version=pyver)]
                if pyver == '2.4':
                    requirements.append(ctypes_requirement(self.get_name(),
                        prefix=scheme_prefix))

                info = dict(self.get_scheme_info(scheme))
                info.update(dict(
                    IFRequirementDicts=requirements,
                    ))

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

            add_package(
                '/System/Library/Frameworks/Python.framework/Versions/2.5',
                '/Library/Python/2.5/site-packages', 
                '2.5', 'pyglet-syspy2.5',
                'pyglet for Python 2.5 in /System/Library')
            add_package(
                '/System/Library/Frameworks/Python.framework/Versions/2.6',
                '/Library/Python/2.6/site-packages', 
                '2.6', 'pyglet-syspy2.6',
                'pyglet for Python 2.6 in /System/Library')
            add_package(
                '/Library/Frameworks/Python.framework/Versions/2.4',
                '/Library/Frameworks/Python.framework/Versions/2.4' \
                    '/lib/python2.4/site-packages',
                '2.4', 'pyglet-py2.4',
                'pyglet for Python 2.4 in /Library')
            add_package(
                '/Library/Frameworks/Python.framework/Versions/2.5',
                '/Library/Frameworks/Python.framework/Versions/2.5' \
                    '/lib/python2.5/site-packages',
                '2.5', 'pyglet-py2.5',
                'pyglet for Python 2.5 in /Library')
            add_package(
                '/Library/Frameworks/Python.framework/Versions/2.6',
                '/Library/Frameworks/Python.framework/Versions/2.6' \
                    '/lib/python2.6/site-packages',
                '2.6', 'pyglet-py2.6',
                'pyglet for Python 2.6 in /Library')
            add_package(
                '/opt/local/',
                '/opt/local/lib/python2.4/site-packages',
                '2.4', 'pyglet-macports-py2.4',
                'pyglet for MacPorts Python 2.4 in /opt/local')
            add_package(
                '/opt/local/',
                '/opt/local/lib/python2.5/site-packages',
                '2.5', 'pyglet-macports-py2.5',
                'pyglet for MacPorts Python 2.5 in /opt/local')
            add_package(
                '/opt/local/',
                '/opt/local/Library/Frameworks/Python.framework/Versions/2.6' \
                    '/lib/python2.6/site-packages',
                '2.6', 'pyglet-macports-py2.6',
                'pyglet for MacPorts Python 2.6 in /opt/local')
 
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

if sys.version_info >= (3,):
    # Automatically run 2to3 when using Python 3
    if _have_setuptools:
        setup_info["use_2to3"] = True
    else:
        from distutils.command.build_py import build_py_2to3
        setup_info["cmdclass"] = {"build_py" : build_py_2to3}

setup(**setup_info)
