#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import sys

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

else:
    from distutils.core import setup
    _have_setuptools = False

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

if _have_setuptools:
    # Additional dict values for setuptools
    install_requires = []
    if sys.version_info < (2, 5, 0):
        install_requires.append('ctypes')
    setuptools_info = dict(
        zip_safe=True,
        install_requires=install_requires,
    )
    setup_info.update(setuptools_info)

setup(**setup_info)
