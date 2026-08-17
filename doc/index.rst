pyglet Documentation
====================

.. note::
   This is the documentation for pyglet version |version|.
   If you need a different one use the docs version selector.

**pyglet** is a cross-platform windowing and multimedia library for Python,
intended for developing games and other visually rich applications. It supports
windowing, user interface event handling, game controllers and joysticks,
OpenGL graphics, loading images and videos, and playing sounds and music.
**pyglet** works on Windows, macOS and Linux.

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

Please join the conversation on our `Discord server <https://discord.gg/QXyegWe>`_.!

.. _Discord: https://discord.gg/QXyegWe

If this is your first time reading about pyglet, we suggest you start at
:doc:`programming_guide/quickstart`.
If you are migrating from an older version of pyglet, please read through
:doc:`programming_guide/migration`.

.. toctree::
   :maxdepth: 3
   :caption: Getting Started

   programming_guide/installation
   programming_guide/quickstart
   programming_guide/examplegame

.. toctree::
   :maxdepth: 3
  :caption: Application Fundamentals

   programming_guide/windowing
   programming_guide/eventloop
   programming_guide/events
   programming_guide/event_chains
   programming_guide/time
   programming_guide/options
   programming_guide/debug

.. toctree::
   :maxdepth: 3
   :caption: Input and User Interface

   programming_guide/keyboard
   programming_guide/mouse
   programming_guide/input
   programming_guide/gui

.. toctree::
   :maxdepth: 3
   :caption: Assets and Media

   programming_guide/resources
   programming_guide/image
   Supported fonts <programming_guide/fonts>
   programming_guide/text
   programming_guide/media

.. toctree::
   :maxdepth: 3
   :caption: Graphics and Rendering

   programming_guide/shapes
   programming_guide/texture
   programming_guide/rendering
   programming_guide/camera
   programming_guide/math
   programming_guide/models

.. toctree::
   :maxdepth: 3
   :caption: Graphics Backends

   programming_guide/context
   programming_guide/gl
   programming_guide/opengles

.. toctree::
   :maxdepth: 3
   :caption: Web and Migration

   programming_guide/pyodide
   Migrating from pyglet 2.1 to 3.0 <programming_guide/migration>
   Migrating from pyglet 2.0 to 2.1 <programming_guide/migration2>
   From pygame to pyglet <programming_guide/from_pygame>

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   modules/pyglet
   modules/app
   modules/clock
   modules/config/index
   modules/display
   modules/customtypes
   modules/enums
   modules/event
   modules/font/index
   modules/graphics/index
   modules/gui
   modules/image/index
   modules/info
   modules/input
   modules/math
   modules/media
   modules/models
   modules/resource
   modules/storage
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
   internal/doc
   internal/testing
   internal/dist
   internal/gl
   internal/generated
   internal/wraptypes
   internal/media_manual
   internal/media_logging_manual
