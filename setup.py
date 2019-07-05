#!/usr/bin/env python
import os
import shutil
import sys
from setuptools import setup, find_packages

# Bump pyglet/__init__.py version as well.
VERSION = '1.4.0'

long_description = '''pyglet provides an object-oriented programming
interface for developing games and other visually-rich applications
for Windows, Mac OS X and Linux.'''

# The source dist comes with batteries included, the wheel can use pip to get the rest
is_wheel = 'bdist_wheel' in sys.argv

excluded = []
if is_wheel:
    excluded.append('extlibs.future')


def exclude_package(pkg):
    for exclude in excluded:
        if pkg.startswith(exclude):
            return True
    return False


def create_package_list(base_package):
    return ([base_package] +
            [base_package + '.' + pkg
             for pkg
             in find_packages(base_package)
             if not exclude_package(pkg)])


setup_info = dict(
    # Metadata
    name='pyglet',
    version=VERSION,
    author='Alex Holkner',
    author_email='Alex.Holkner@gmail.com',
    url='http://pyglet.readthedocs.org/en/latest/',
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
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
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

if is_wheel:
    setup_info['install_requires'] = ['future']

setup(**setup_info)
