[![pypi](https://badge.fury.io/py/pyglet.svg)](https://pypi.python.org/pypi/pyglet)

# pyglet

pyglet provides an easy to use Pythonic interface for developing games
and other visually-rich applications on Windows, Mac OS X and Linux.

* [Pyglet Documentation](https://pyglet.readthedocs.io/en/latest/)
* [Pyglet Wiki](https://github.com/pyglet/pyglet/wiki)
* [Pyglet on PyPI](https://pypi.org/project/pyglet/)
* [Pyglet Discord Server](https://discord.gg/QXyegWe)
* [Pyglet mailing list](http://groups.google.com/group/pyglet-users)
* [Pyglet Website](http://pyglet.org/)

Pyglet has an active developer and user community.  If you find a bug, please [open an issue](https://github.com/pyglet/pyglet/issues).

## Requirements

pyglet runs under Python 2.7, and 3.4+. The entire codebase is fully 2/3 dual
compatible, making use of the future module for backwards compatibility with
legacy Python. Being written in pure Python, it also works on other Python
interpreters such as PyPy. Supported platforms are:

* Windows XP or later
* Mac OS X 10.3 or later
* Linux, with the following libraries (most recent distributions will have
  these in a default installation):
  * OpenGL and GLX
  * GDK 2.0+ or PIL (required for loading images other than PNG and BMP)
  * OpenAL or Pulseaudio (required for playing audio)

Please note that pyglet v1.4 will likely be the last version to support
Python 2.7. Future releases of pyglet will be Python 3 only, and will be
targeting OpenGL 3.3+. Previous releases will remain available for download.

## Installation

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

## Testing

pyglet makes use of pytest for its test suite.

    py.test tests/

Please check the documentation for more information about running and writing tests.
