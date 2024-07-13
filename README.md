[![pypi](https://badge.fury.io/py/pyglet.svg)](https://pypi.python.org/pypi/pyglet) [![rtd](https://readthedocs.org/projects/pyglet/badge/?version=latest)](https://pyglet.readthedocs.io) [![PyTest](https://github.com/pyglet/pyglet/actions/workflows/unittests.yml/badge.svg)](https://github.com/pyglet/pyglet/actions/workflows/unittests.yml)

![logo_large.png](https://github.com/pyglet/pyglet/blob/54a8c8b7e701b1692c6a10dd80f94ec837c27bd3/examples/opengl/pyglet.png)

# pyglet

*pyglet* is a cross-platform windowing and multimedia library for Python, intended for developing games
and other visually rich applications. It supports Windowing, input event handling, Controllers & Joysticks,
OpenGL graphics, loading images and videos, and playing sounds and music. *pyglet* works on Windows, OS X and Linux.

> :exclamation: :exclamation: A major pyglet update has just been released (v2.0). This brings many 
> new exciting features, but also some necessary breaking changes. If your game/application has suddenly 
> stopped working, please read the [migration section in the documentation](https://pyglet.readthedocs.io/en/latest/programming_guide/migration.html)
> The previous version of pyglet is tracked in the `pyglet-1.5-maintenance` branch.
> **If you want to do a pull request for the previous release, please target the appropriate branch**. 

> :exclamation: `pyglet.graphics.draw` and `pyglet.graphics.draw_indexed` will be removed
> in pyglet v2.1. The `shapes` module is an alternative for drawing simple shapes. 

* pyglet [documentation]
* pyglet on [PyPI]
* pyglet [discord] server
* pyglet [mailing list]
* pyglet [issue tracker]
* pyglet [website]

pyglet has an active developer and user community.  If you find a bug or a problem with the documentation,
please [open an issue](https://github.com/pyglet/pyglet/issues).
Anyone is welcome to join our [discord] server where a lot of the development discussion is going on.
It's also a great place to ask for help.

Some features of pyglet are:

* **No external dependencies or installation requirements.** For most application and game requirements, *pyglet*
  needs nothing else besides Python, simplifying distribution and installation. It's easy to package and distribute
  your project with [Nuitka](https://nuitka.net) or [PyInstaller](https://pyinstaller.org). 
* **Take advantage of multiple windows and multi-monitor desktops.** *pyglet* allows you to use multiple
  platform-native windows, and is fully aware of multi-monitor setups for use with fullscreen games.
* **Load images, sound, music and video in almost any format.** *pyglet* can optionally use FFmpeg to play back
  audio formats such as MP3, OGG/Vorbis and WMA, and video formats such as MPEG2, H.264, H.265, WMV and Xvid.
  Without FFmpeg, *pyglet* contains built-in support for standard formats such as wav, png, bmp, and others.
* **pyglet is written entirely in pure Python**, and makes use of the *ctypes* module to interface with system
  libraries. You can modify the codebase or make a contribution without any second language compilation steps or
  compiler setup. Despite being pure Python, *pyglet* has excellent performance thanks to advanced batching for
  drawing thousands of objects.
* **pyglet is provided under the BSD open-source license**, allowing you to use it for both commercial and other
  open-source projects with very little restriction.

## Requirements

pyglet runs under Python 3.8+. Being written in pure Python, it also works on other Python interpreters such as PyPy. Supported platforms are:

* Windows 7 or later
* Mac OS X 10.3 or later
* Linux, with the following libraries (most recent distributions will have
  these in a default installation):
  * OpenGL and GLX
  * GDK 2.0+ or Pillow (required for loading images other than PNG and BMP)
  * OpenAL or Pulseaudio (required for playing audio)

**As of pyglet 2.0, OpenGL 3.3+ is required**. 

To play a large variety of compressed audio and video files,
pyglet can optionally take advantage of [FFmpeg](https://ffmpeg.org/).

## Installation

pyglet is installable from PyPI:

    pip install --upgrade --user pyglet

## Installation from source

If you're reading this `README` from a source distribution, you can install pyglet with:

    pip install --upgrade --user .
    # or
    python setup.py install --user

You can also install the latest development version directly from Github:

    pip install --upgrade --user https://github.com/pyglet/pyglet/archive/master.zip

For local development install pyglet in editable mode:

```bash
# with pip
pip install -e .
# with setup.py
python setup.py develop
```

There are no compilation steps during the installation; if you prefer,
you can simply add this directory to your `PYTHONPATH` and use pyglet without
installing it. You can also copy pyglet directly into your project folder.

## Contributing

**A good way to start contributing to a component of pyglet is by its documentation**. When studying the code you
are going to work with, also read the associated docs. If you don't understand the code with the help of the docs,
it is a sign that the docs should be improved. If you wish to make large changes to any part of pyglet, it's always
a good idea to reach out for feedback first. This can avoid wasted effort in cases where someone is already working
on something similar, or if your idea can't be accepted for any reason. 

A basic outline of how to a contribution is as follows:

* Fork the [official repository](https://github.com/pyglet/pyglet/fork).
* In your fork, checkout the branch you wish to contribute to (such as *pyglet-1.5-maintenance*).
* Apply your changes to your fork.
* Submit a [pull request](https://github.com/pyglet/pyglet/pulls) describing the changes you have made.
* Alternatively you can create a patch and submit it to the issue tracker.

When making a pull request, check that you have addressed its respective documentation, both within the code docstrings
and the programming guide (if applicable). It is very important to all of us that the documentation matches the latest
code and vice-versa.

Consequently, an error in the documentation, either because it is hard to understand or because it doesn't match the
code, is a bug that deserves to be reported on a ticket.

## Building Docs

[Documentation and Type Hints]: https://pyglet.readthedocs.io/en/latest/internal/doc.html

To get started quickly:

    pip install -r doc/requirements.txt
    python make.py docs

Please check [Documentation and Type Hints][] guide to learn more.

## Testing

pyglet makes use of pytest for its test suite.

```bash
pip install -r tests/requirements.txt --user
# Only run unittests
pytest tests/unit
```

Please check the [testing section in the development guide](https://pyglet.readthedocs.io/en/latest/internal/testing.html)
for more information about running and writing tests.

## Contact

pyglet is developed by many individual volunteers, and there is no central point of contact. If you have a question
about developing with pyglet, or you wish to contribute, please join the [mailing list], [discord] server, or [subreddit].

For legal issues, please contact [Alex Holkner](mailto:Alex.Holkner@gmail.com).

[discord]: https://discord.gg/QXyegWe
[mailing list]: http://groups.google.com/group/pyglet-users
[subreddit]: https://www.reddit.com/r/pyglet/
[documentation]: https://pyglet.readthedocs.io
[wiki]:  https://github.com/pyglet/pyglet/wiki
[pypi]:  https://pypi.org/project/pyglet/
[website]: http://pyglet.org/
[issue tracker]: https://github.com/pyglet/pyglet/issues
