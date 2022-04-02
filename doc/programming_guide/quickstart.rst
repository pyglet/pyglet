.. _quickstart:

Writing a pyglet application
============================

Getting started with a new library or framework can be daunting, especially
when presented with a large amount of reference material to read.
This chapter gives a very quick introduction to pyglet without going into
too much detail.

Hello, World
------------

We'll begin with the requisite "Hello, World" introduction. This program will
open a window with some text in it and wait to be closed. You can find the
entire program in the `examples/programming_guide/hello_world.py` file.

Begin by importing the :mod:`pyglet` package::

    import pyglet

Create a :class:`pyglet.window.Window` by calling its default constructor.
The  window will be visible as soon as it's created, and will have reasonable
default  values for all its parameters::

    window = pyglet.window.Window()

To display the text, we'll create a :class:`~pyglet.text.Label`. Keyword
arguments are used to set the font, position and anchorage of the label::

    label = pyglet.text.Label('Hello, world',
                              font_name='Times New Roman',
                              font_size=36,
                              x=window.width//2, y=window.height//2,
                              anchor_x='center', anchor_y='center')

An :meth:`~pyglet.window.Window.on_draw` event is dispatched to the window
to give it a chance to redraw its contents.  pyglet provides several ways to
attach event handlers to objects; a simple way is to use a decorator::

    @window.event
    def on_draw():
        window.clear()
        label.draw()

Within the :meth:`~pyglet.window.Window.on_draw` handler the window is cleared
to the default background color (black), and the label is drawn.

Finally, call::

    pyglet.app.run()

This will enter pyglet's default event loop, and let pyglet respond to
application events such as the mouse and keyboard.
Your event handlers will now be called as required, and the
:func:`~pyglet.app.run` method will return only when all application
windows have been closed.

If you are coming from another library, you may be used to writing your
own event loop. This is possible to do with pyglet as well, but it is
generally discouraged; see :ref:`programming-guide-eventloop` for details.

Image viewer
------------

Most games and applications will need to load and display images on the
screen. In this example we'll load an image from the application's
directory and display it within the window::

    import pyglet

    window = pyglet.window.Window()
    image = pyglet.resource.image('kitten.jpg')

    @window.event
    def on_draw():
        window.clear()
        image.blit(0, 0)

    pyglet.app.run()

We used the :func:`~pyglet.resource.image` function of :mod:`pyglet.resource`
to load the image, which automatically locates the file relative to the source
file (rather than the working directory).  To load an image not bundled with
the application (for example, specified on the command line), you would use
:func:`pyglet.image.load`.

The :meth:`~pyglet.image.AbstractImage.blit` method draws the image.  The
arguments ``(0, 0)`` tell pyglet to draw the image at pixel coordinates 0,
0 in the window (the lower-left corner).

The complete code for this example is located in
`examples/programming_guide/image_viewer.py`.

Handling mouse and keyboard events
----------------------------------

So far the only event used is the :meth:`~pyglet.window.Window.on_draw`
event.  To react to keyboard and mouse events, it's necessary to write and
attach event handlers for these events as well::

    import pyglet

    window = pyglet.window.Window()

    @window.event
    def on_key_press(symbol, modifiers):
        print('A key was pressed')

    @window.event
    def on_draw():
        window.clear()

    pyglet.app.run()

Keyboard events have two parameters: the virtual key `symbol` that was
pressed, and a bitwise combination of any `modifiers` that are present (for
example, the ``CTRL`` and ``SHIFT`` keys).

The key symbols are defined in :mod:`pyglet.window.key`::

    from pyglet.window import key

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == key.A:
            print('The "A" key was pressed.')
        elif symbol == key.LEFT:
            print('The left arrow key was pressed.')
        elif symbol == key.ENTER:
            print('The enter key was pressed.')

See the :mod:`pyglet.window.key` documentation for a complete list
of key symbols.

Mouse events are handled in a similar way::

    from pyglet.window import mouse

    @window.event
    def on_mouse_press(x, y, button, modifiers):
        if button == mouse.LEFT:
            print('The left mouse button was pressed.')

The ``x`` and ``y`` parameters give the position of the mouse when the button
was pressed, relative to the lower-left corner of the window.

There are more than 20 event types that you can handle on a window. An easy
way to find the event names and parameters you need is to add the following
lines to your program::

    event_logger = pyglet.window.event.WindowEventLogger()
    window.push_handlers(event_logger)

This will cause all events received on the window to be printed to the
console.

An example program using keyboard and mouse events is in
`examples/programming_guide/events.py`

Playing sounds and music
------------------------

pyglet makes it easy to play and mix multiple sounds together.
The following example plays an MP3 file [#mp3]_::

    import pyglet

    music = pyglet.resource.media('music.mp3')
    music.play()

    pyglet.app.run()

As with the image loading example presented earlier,
:func:`~pyglet.resource.media` locates the sound file in the application's
directory (not the working directory).  If you know the actual filesystem path
(either relative or absolute), use :func:`pyglet.media.load`.

By default, audio is streamed when playing. This works well for longer music
tracks. Short sounds, such as a gunfire shot used in a game, should instead be
fully decoded in memory before they are used. This allows them to play more
immediately and incur less of a CPU performance penalty. It also allows playing
the same sound repeatedly without reloading it.
Specify ``streaming=False`` in this case::

    sound = pyglet.resource.media('shot.wav', streaming=False)
    sound.play()

The `examples/media_player.py` example demonstrates playback of streaming
audio and video using pyglet.  The `examples/noisy/noisy.py` example
demonstrates playing many short audio samples simultaneously, as in a game.

.. [#mp3] MP3 and other compressed audio formats require FFmpeg to be
          installed.
          Uncompressed WAV files can be played without FFmpeg.

Where to next?
--------------

The examples above have shown you how to display something on the screen,
and perform a few basic tasks.  You're probably left with a lot of questions
about these examples, but don't worry. The remainder of this programming guide
goes into greater technical detail on many of pyglet's features.  If you're
an experienced developer, you can probably dive right into the sections that
interest you.

For new users, it might be daunting to read through everything all at once.
If you feel overwhelmed, we recommend browsing through the beginnings of each
chapter, and then having a look at a more in-depth example project.
You can find an example of a 2D game in the :ref:`programming-guide-game`
section.

To write advanced 3D applications or achieve optimal performance in your 2D
applications, you'll need to work with OpenGL directly.  If you only want to
work with OpenGL primitives, but want something slightly higher-level, have a
look at the :ref:`guide_graphics` module.

There are numerous examples of pyglet applications in the ``examples/``
directory of the documentation and source distributions.  If you get
stuck, or have any questions, join us on the `mailing list`_ or `Discord`_!

.. _mailing list: http://groups.google.com/group/pyglet-users
.. _Discord: https://discord.gg/QXyegWe
