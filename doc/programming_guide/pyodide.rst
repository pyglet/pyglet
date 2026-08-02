Pyodide and browsers
====================

Pyodide makes it possible to run a pyglet application in a web browser.
pyglet uses WebGL 2 for drawing and browser APIs for input, fonts, and audio.
The Python side of an application can usually keep its familiar structure::

    import pyglet

    window = pyglet.window.Window()

    @window.event
    def on_draw():
        window.clear()

    pyglet.app.run()

Browser support is still developing. Automated tests currently run in
Chromium, so applications should also be tested in any other browsers they
intend to support. pyglet is currently developed and tested with Pyodide
|pyodide_version|.

Launching an application
------------------------

Before Python starts, the web page or build tool needs to load Pyodide, add the
application and its assets to Pyodide's file system, and load any optional
packages. The example in ``tools/pyodide`` shows one way to do this, but pyglet
does not depend on that particular tool or page layout.

pyglet currently needs access to the page's DOM, so Pyodide must run on the
main browser thread rather than in a Web Worker.

Use ``pyodide.runPythonAsync`` to launch the application. ``runpy.run_path`` is
a convenient way to give the main file the same ``__file__`` and ``__main__``
behavior it has when run normally::

    await pyodide.runPythonAsync(
        "import runpy\nrunpy.run_path('/app/main.py', run_name='__main__')"
    );

During development, serve the project over HTTP. Browsers normally prevent a
page opened with ``file://`` from fetching the files it needs.

Files and packages
------------------

Browser Python cannot freely access files on the visitor's computer. Package
application assets with the web project and copy them into Pyodide's virtual
file system before the application starts. Once there, they can be loaded with
``pyglet.resource``, ``pathlib``, or ``open`` in the usual way.

Packages provided by Pyodide can also be loaded before starting Python. For
example, Pillow adds support for more image formats::

    await pyodide.loadPackage("pillow");

Pure Python wheels will often work through ``micropip``. Packages containing
native extensions need a build made specifically for Pyodide.

Saving data
^^^^^^^^^^^

Pyodide's default file system lives in memory. Files written there disappear
when the page is reloaded.

In a browser, ``pyglet.resource.get_settings_path("my-game")`` and
``pyglet.resource.get_data_path("my-game")`` both use ``/data/my-game``. The
path alone does not make the files persistent. The page or build tool must
mount persistent browser storage at ``/data``, restore it before the
application reads its saves, and synchronize it after writing them. An
IndexedDB-backed Pyodide file system is one way to provide this.

Storage synchronization is asynchronous, so avoid doing it during a
time-sensitive update or draw. A file chosen through a browser file picker is
also not automatically persistent; the application must save a copy if it
needs the file after a reload.

The application loop
--------------------

Drawing and updates
^^^^^^^^^^^^^^^^^^^

The browser decides when a window is drawn through ``requestAnimationFrame``.
This normally follows the display refresh rate and may pause when the tab is
hidden. The ``interval`` passed to ``pyglet.app.run`` does not change the
browser's refresh rate. Passing ``None`` disables automatic drawing.

Scheduled functions remain independent of drawing. They can run faster or
slower than the display rate::

    def update(dt):
        player.x += player.speed * dt

    pyglet.clock.schedule_interval(update, 1 / 120)

Browsers may delay timers, particularly in a background tab. Use the supplied
``dt`` when updating state rather than assuming that every call arrived at the
requested interval.

Behavior of ``pyglet.app.run``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On desktop, ``pyglet.app.run()`` blocks until the application exits. Blocking
the browser's main thread would stop the page from working, so the Pyodide
version starts pyglet's loop and returns immediately. Code placed after
``pyglet.app.run()`` therefore runs immediately in the browser.

Do application setup before calling ``run``. If work must happen when the
application closes, use an ``on_exit`` handler::

    @pyglet.app.event_loop.event
    def on_exit():
        save_if_needed()

A long-running Python function can still make the page unresponsive. Break
large jobs into scheduled pieces, or use an asynchronous browser API when
waiting for a network request. Most pyglet applications do not otherwise need
to manage Pyodide's asyncio loop themselves.

Browser networking follows the same security rules as JavaScript. HTTP
requests are subject to CORS, and ordinary desktop socket behavior may not be
available. ``pyodide.http.pyfetch`` is suitable for asynchronous browser
requests.

Windows and input
-----------------

pyglet uses a canvas named ``pygletCanvas`` by default and creates it if
necessary. To draw into a canvas already present on the page, set its ID before
creating the window::

    import pyglet
    pyglet.options.pyodide.canvas_id = "game-canvas"

    window = pyglet.window.Window()

The canvas can have a different CSS size and framebuffer size on a high-DPI
display. Use ``window.get_framebuffer_size()`` when pixel dimensions are
needed.

The browser controls vertical synchronization, so ``window.set_vsync`` cannot
change the draw rate. The window caption is used as the page title.

Fullscreen, exclusive mouse mode, and audio playback may require a click or
another user action. Request these features from an input handler and allow for
the browser to reject the request.

File drops and file pickers
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass ``file_drops=True`` when creating a window to receive browser file drops::

    window = pyglet.window.Window(file_drops=True)

    @window.event
    def on_file_drop(x, y, paths):
        for path in paths:
            load_document(path)

Browser files are copied into a temporary directory in Pyodide's file system
before ``on_file_drop`` is called. The paths are therefore safe to pass to
``open``, but they are not paths on the visitor's
computer and disappear when the page is reloaded.

``pyglet.window.dialog.FileOpenDialog`` uses the browser's file picker and
reports files in the same way. Open it directly from a click or key handler,
because browsers require a user action before showing a picker. Browser pickers
cannot choose an initial directory. ``FileSaveDialog`` is not currently
available because a browser cannot return a writable operating-system path.

Clipboard
^^^^^^^^^

With the canvas focused, the normal copy and paste shortcuts work for pyglet
text input. Pasted text is delivered through ``on_text``. Browser
clipboard permissions mean that ``get_clipboard_text`` can only return the
latest text received or set by pyglet, while ``set_clipboard_text`` attempts
to update the system clipboard when the browser permits it.

Touch input, tablets, raw input devices, and the legacy joystick API are not
currently supported. Controllers use the browser Gamepad API and its standard
mapping. Rumble availability depends on the browser and device.

Fonts
-----

``pyglet.font.add_file`` can load a font from Pyodide's file system, but the
browser finishes loading it asynchronously. Register ``on_font_loaded`` before
adding the file, then create or update any text that uses it::

    label = pyglet.text.Label("Loading...", font_name="sans-serif")

    @pyglet.font.manager.event
    def on_font_loaded(name, weight, style, stretch):
        if name == "Action Man":
            label.font_name = name

    pyglet.font.add_file("/app/fonts/action_man.ttf")

A custom font can also be loaded by JavaScript before the Python application
starts. It will then be available to pyglet immediately::

    const font = new FontFace("Action Man", "url(fonts/action_man.ttf)");
    await font.load();
    document.fonts.add(font);
    await document.fonts.load('16px "Action Man"');

    await pyodide.runPythonAsync(pythonApplication);

The family passed to ``FontFace`` is the name used by pyglet. Handle font load
errors in JavaScript because browsers can silently substitute another font.
Browser text is always anti-aliased, so ``pyglet.options.text_antialiasing``
does not apply.

Images, audio, and graphics
---------------------------

PNG and BMP images work without optional packages. Load Pillow before starting
the application for additional image formats.

Audio uses the Web Audio API and is decoded into memory rather than streamed.
The browser determines which of MP3, AAC, WAV, OGG, and WebM it can decode.
Audio may remain suspended until the visitor interacts with the page. Seeking
and restarting a stopped source are not currently supported by pyglet's
browser audio driver.


Platform checks
---------------

Use ``pyglet.compat_platform == "emscripten"`` when browser-specific behavior
is needed. Keeping the rest of the application platform-neutral makes it much
easier to run the same code on desktop and in a browser.

For more detail on the underlying environment, see Pyodide's `file-system
guide <https://pyodide.org/en/stable/usage/file-system.html>`_, `package guide
<https://pyodide.org/en/stable/usage/packages-in-pyodide.html>`_, and
`WebLoop reference <https://pyodide.org/en/stable/usage/api/python-api/webloop.html>`_.
