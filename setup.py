#!/usr/bin/env python
import sys
from setuptools import setup, find_packages

# Bump pyglet/__init__.py version as well.
VERSION = '1.3.0rc1'

long_description = '''pyglet provides an object-oriented programming
interface for developing games and other visually-rich applications
for Windows, Mac OS X and Linux.'''

# The source dist comes with batteries included, the wheel can use pip to get the rest.
is_wheel = 'bdist_wheel' in sys.argv


# The pyglet.extlibs.future package is not detected by find_packages,
# so it must be included as flat files (if installing from source).

if is_wheel:
    bundle_extlibs_future = False
    requirements = ['future']
else:
    bundle_extlibs_future = True
    requirements = []


def create_package_list(base_package):
    return [base_package] + [base_package + '.' + pkg for pkg in find_packages(base_package)]


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
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # Package info
    packages=create_package_list('pyglet'),
    include_package_data=bundle_extlibs_future,
    install_requires=requirements,

    # Add underscore prefix to the names of temporary build dirs
    options={'build': {'build_base': '_build'}},

    zip_safe=True,
)


setup(**setup_info)
