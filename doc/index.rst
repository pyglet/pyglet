pyglet Documentation
====================

**pyglet** is a cross-platform windowing and multimedia library for Python,
intended for developing games and other visually rich applications. It supports
windowing, user interface event handling, game controllers and joysticks,
OpenGL graphics, loading images and videos, and playing sounds and music.
**pyglet** works on Windows, OS X and Linux.

Some of the features of pyglet are:

* **No external dependencies or installation requirements.** For most
  application and game requirements, pyglet needs nothing else besides Python,
  simplifying distribution and installation.
* **Take advantage of multiple windows and multi-monitor desktops.** pyglet
  allows you to use as many windows as you need, and is fully aware of
  multi-monitor setups for use with fullscreen games and applications.
* **Load images, sound, music and video in almost any format.** pyglet has
  built-in support for common audio and image formats, and can optionally use
  ffmpeg to load almost any other compressed audio or video files.
* **pyglet is provided under the BSD open-source license**, allowing you to
  use it for both commercial and other open-source projects with very little
  restriction.

Please join our `Discord` server, or join us on the `mailing list`_!

.. _Discord: https://discord.gg/QXyegWe
.. _mailing list: http://groups.google.com/group/pyglet-users

If this is your first time reading about pyglet, we suggest you start at
:doc:`programming_guide/quickstart`.

.. toctree::
   :maxdepth: 3
   :caption: Programming Guide

   programming_guide/installation
   programming_guide/quickstart
   programming_guide/windowing
   programming_guide/keyboard
   programming_guide/mouse
   programming_guide/input
   programming_guide/graphics
   programming_guide/shapes
   programming_guide/text
   programming_guide/image
   programming_guide/media
   programming_guide/resources
   programming_guide/events
   programming_guide/time
   programming_guide/context
   programming_guide/gl
   programming_guide/eventloop
   programming_guide/options
   programming_guide/debug
   programming_guide/advanced
   programming_guide/examplegame

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   modules/pyglet
   modules/app
   modules/canvas
   modules/clock
   modules/event
   modules/font
   modules/gl
   modules/graphics/index
   modules/gui
   modules/image/index
   modules/info
   modules/input
   modules/media
   modules/resource
   modules/sprite
   modules/shapes
   modules/text/index
   modules/window

.. toctree::
   :maxdepth: 3
   :caption: External Resources

   external_resources

.. toctree::
   :maxdepth: 3
   :caption: Development Guide

   internal/contributing
   internal/virtualenv
   internal/testing
   internal/doc
   internal/dist
   internal/gl
   internal/generated
   internal/wraptypes
   internal/media_manual
   internal/media_logging_manual
