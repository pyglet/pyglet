Pyodide Integration
===================
Basic support for pyodide has been added as of version 3.0. This will allow the pyglet to be run inside a browser
environment. Support for this is extremely limited, as it relies upon another project to be functional.

Currently only WebGL2 is supported. Tested via Chrome (138.0.7204.50) and Edge (138.0.3351.65).

Limitations
-----------
While users generally will not have to work with JavaScript in relation to your pyglet script, there are programming
differences between the Python and JavaScript language itself that impacts users.

Below is a list of information to keep in mind when working with both JavaScript and Pyglet.

Asynchronous Behavior
^^^^^^^^^^^^^^^^^^^^^
JavaScript (and Pyodide) relies on asynchronous behavior, which is very different than how Python operates
normally.

Although there is an ``asyncio`` standard module, it requires rethinking how you program. Many libraries are not
created with asynchronous behavior in mind. Generally many functions will assume that a prior function or call
was completed successfully before it runs. This assumption is where a lot of things break down.

While most of this behavior has been insulated from the user, there are still areas where this can affect your
application which requires specific handling.

Custom fonts
^^^^^^^^^^^^
In most operating systems, when a font is loaded, the operations are done synchronously. This means after
we have successfully called and executed adding the data, it will be ready to use immediately after.

For example::

    with open("action_man.ttf", 'rb') as f:
       pyglet.font.add_file(f)

    font = pyglet.font.load("Action Man", 12)

    label = pyglet.text.Label("Hello, world!", font_name="Action Man")

For a browser to see the custom font, it has to be loaded through JavaScript and into the browser. This loading process
is done asynchronously.

In the example above, although the loading of the custom font has been started, there is no guarantee it is ready by the
time the label is created. To resolve this, a dispatcher was created that will notify the user when a custom font is
ready::

    @pyglet.font.manager.event
    def on_font_loaded(font_family_name: str, weight: str, italic: str, stretch: str) -> None:
        # If the font loaded matches what you want for your label, assign it.
        if font_family_name == "Action Man":
            label.font_name = "Action Man"

This can be useful if you want to either wait to create text until the font is ready, or update existing text with the
proper font.

.. note:: ``pyglet.options.text_antialiasing`` is not supported. Browsers can not render text without anti-aliasing.

Audio
^^^^^
Audio is also loaded asynchronously with JavaScript through the Web Audio API.

Audio can be kept the same as a normal application (``media.play()``). Pyglet will create the resources necessary to
output audio. However, :py:class:`~pyglet.media.AudioPlayer` still relies on a callback from JavaScript Web Audio that
the data is decoded and ready. When it's ready, the player will immediately load the data into the buffer and output, so
long as it is active. In testing, this has not been noticeable, but it is recommended to load the audio at the beginning
of your application.

.. warning:: Web Audio does not allow a player to restart playback of a source once stopped, nor seek.

.. note:: Web Audio sources are not streaming, it should be considered a :py:class:`~pyglet.media.StaticSource` at all times.

Images
^^^^^^
Image decoding is also asynchronous in JavaScript API's, but not used in Pyglet.

Normally this would require a similar callback system as the custom fonts where pyglet has to submit data to JavaScript
APIs and wait for a callback to notify the user when it's ready. However, Pyglet will instead use Python only decoders
to improve speed and compatibility. Through testing, decoding images is actually much slower through the
JavaScript API than what Python and Pyglet can provide.

Pyglet only supports `PNG` and `BMP` image formats without any dependencies.

For further image extension support, it is recommended to ``import PIL`` (pillow). Pyodide provides a supported version
in their distribution. It can be loaded through JavaScript via ``await pyodide.loadPackage("pillow")``. Pyglet will
utilize Pillow as the default image decoder when found.

File System
^^^^^^^^^^^
Pyodide utilizes a "Virtual File System" or VFS. For more information visit: https://pyodide.org/en/stable/usage/file-system.html

In short, the browser or Pyodide does not access your local files the same way as a normal application does. It can only
access what is in the VFS. The ``pyglet.resource`` module, ``pathlib``, and ``os`` module typically only can see this
structure.

Users will need to configure Pyodide to copy files into the VFS via ``pyodide.FS.writeFile``. For a simple example of
making a project available in a browser, see the following example script in our tools folder: https://github.com/pyglet/pyglet/tree/development/tools/pyodide

.. note:: The VFS data only exists per browser session, so refreshing the browser will clear the VFS and require it
          to be loaded again.


Platform
^^^^^^^^
Pyglet differentiates the browser environment through the ``pyglet.compat_platform`` property. Through pyodide,
this is reported as ``emscripten``. If you want branching behavior depending on the operating system, it is recommended
to use that property.


pyglet.app.run
^^^^^^^^^^^^^^
In normal Pyglet operation, the way a typical platform event loop behaves is that operating system API calls are made to
wait for an event to occur with a small timeout. This will prevent high CPU usage, and allow scheduled calls to be
independent of the window refresh rate.

Pyglet will utilize an asyncio loop for scheduled events, and ``requestAnimationFrame`` from JavaScript for the canvas
refresh rate. See:: https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
this refresh rate is determined by the browser and cannot be modified by pyglet.

If you want your event loop to rely on ``requestAnimationFrame`` for precision, you can start your pyglet application
via ``pyglet.app.run(None)``.  Otherwise, the existing usage can be left.

.. warning:: A memory leak exists in Pyodide version 0.27.7 with asyncio. It is recommended to use ``pyglet.app.run(None)``
             until this is resolved.

Controllers
^^^^^^^^^^^
JavaScript utilizes the Gamepad API, which may differ slightly from the SDL Controller API that pyglet utilizes.

From testing, detection and mapping between controllers were accurate and consistent.

To see how the Javascript Gamepad API maps controls via the "Standard Gamepad" profile, you can
visit: https://w3c.github.io/gamepad/#remapping

Currently re-mapping this "Standard Gamepad" layout is not supported.


Window
^^^^^^
Pyglet uses the following canvas id by default: ``pygletCanvas`` for events and drawing. If this is not found, it will
be created. Pyglet can treat an existing canvas as its own by changing the ``pyglet.options.pyodide.canvas_id`` name.