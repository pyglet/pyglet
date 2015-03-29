#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import shutil
import sys
from setuptools import setup, find_packages

# Bump pyglet/__init__.py version as well.
VERSION = '1.2.3a1'

long_description = '''pyglet provides an object-oriented programming
interface for developing games and other visually-rich applications
for Windows, Mac OS X and Linux.'''

def create_package_list(base_package):
    return ([base_package] +
            [base_package + '.' + pkg for pkg in find_packages(base_package)])


setup_info = dict(
    # Metadata
    name='pyglet',
    version=VERSION,
    author='Alex Holkner',
    author_email='Alex.Holkner@gmail.com',
    url='http://pyglet.readthedocs.org/en/pyglet-1.2-maintenance/',
    download_url='http://pypi.python.org/pypi/pyglet',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # Package info
    packages=create_package_list('pyglet'),

    # Add _ prefix to the names of temporary build dirs
    options={
        'build': {'build_base': '_build'},
        #        'sdist': {'dist_dir': '_dist'},
    },
    zip_safe=True,
)


if sys.version_info >= (3,):
    # Automatically run 2to3 when using Python 3
    setup_info["use_2to3"] = True

setup(**setup_info)
