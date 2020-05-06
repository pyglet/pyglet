Making a pyglet release
=======================

#. Clone pyglet into a new directory

#. Make sure it is up to date::

    git pull

#. Update version string in the following files and commit:

   * pyglet/__init__.py
   * doc/conf.py

#. Tag the current changelist with the version number::

    git tag -a v0.0.0 -m "release message"

#. Push the changes to the central repo::

    git push
    git push --tags

#. Build the wheels and documentation::

    ./make.py clean
    ./make.py dist

#. Upload the wheels and zips to PyPI::

    twine upload dist/pyglet-x.y.z*

#. Start a build of the documentation on https://readthedocs.org/projects/pyglet/builds/

#. Draft a new release on Github, using the same version number https://github.com/pyglet/pyglet/releases

#. Tell people!

Major version increase
----------------------
When preparing for a major version you might also want to consider the
following:

* Create a maintenance branch for the major version
* Add a readthedocs configuration for that maintenance branch
* Point the url in setup.py to the maintenance branch documentation

