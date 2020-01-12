#!/usr/bin/env python
import sys
from setuptools import setup, find_packages

# Parse version number from pyglet/__init__.py:
with open('pyglet/__init__.py') as f:
    info = {}
    for line in f.readlines():
        if line.startswith('version'):
            exec(line, info)
            break

    
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
    version=info['version'],
    author='Alex Holkner',
    author_email='Alex.Holkner@gmail.com',
    url='http://pyglet.readthedocs.org/en/latest/',
    download_url='http://pypi.python.org/pypi/pyglet',
    project_urls={
        'Documentation': 'https://pyglet.readthedocs.io/en/latest',
        'Source': 'https://github.com/pyglet/pyglet',
        'Tracker': 'https://github.com/pyglet/pyglet/issues',
    },
    description='Cross-platform windowing and multimedia library',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # Package info
    packages=create_package_list('pyglet'),

    # Add _ prefix to the names of temporary build dirs
    options={'build': {'build_base': '_build'}, },
    zip_safe=True,
)

if is_wheel:
    setup_info['install_requires'] = ['future']

setup(**setup_info)
