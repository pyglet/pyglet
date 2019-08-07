.. image:: https://badge.fury.io/py/pyglet.svg
   :target: https://pypi.python.org/pypi/pyglet

pyglet
======

pyglet provides an object-oriented programming interface for developing games
and other visually-rich applications for Windows, Mac OS X and Linux.

* `Pyglet Documentation <https://pyglet.readthedocs.io/en/latest/>`_
* `Pyglet Wiki <https://github.com/pyglet/pyglet/wiki>`_
* `Pyglet on PyPI <https://pypi.org/project/pyglet/>`_
* `Pyglet Discord Server <https://discord.gg/QXyegWe>`_
* `Pyglet mailing list <http://groups.google.com/group/pyglet-users>`_
* `Pyglet Website <http://pyglet.org/>`_

Pyglet has an active developer and user community.  If you find a bug, please
`open an issue <https://github.com/pyglet/pyglet/issues>`_.

Requirements
------------

pyglet runs under Python 2.7, and 3.4+. The entire codebase is fully 2/3 dual
compatible, making use of the future module for backwards compatibility with
legacy Python. Being written in pure Python, it also works on other Python
interpreters such as PyPy. pyglet works on the following operating systems:

* Windows XP or later
* Mac OS X 10.3 or later
* Linux, with the following libraries (most recent distributions will have
  these in a default installation):

  * OpenGL and GLX
  * GDK 2.0+ or PIL (required for loading images other than PNG and BMP)
  * OpenAL or Pulseaudio (required for playing audio)

Installation
------------

If you're reading this README from a source distribution, you can install
pyglet with:

    python setup.py install

pyglet is also pip installable from PyPi:

    pip install --upgrade pyglet --user

There are no compilation steps during the installation; if you prefer,
you can simply add this directory to your PYTHONPATH and use pyglet without
installing it. You can also copy pyglet directly into your project folder.

If you want to build the documentation yourself, please check the README file
in the doc directory.

Testing
-------

pyglet makes use of pytest for it's test suite.

    py.test tests/

Please check the documentation for more information about running and writing
tests.
