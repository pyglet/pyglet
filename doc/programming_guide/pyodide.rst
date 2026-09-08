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

In a browser, :mod:`pyglet.storage` keeps saves and settings in the
IndexedDB-backed ``/data`` mount. Its ``cache`` location is in ``/cache``, an
Origin Private File System (OPFS) mount. Cache files survive a refresh, but
applications must be prepared to recreate them when the browser purges storage.

Storage synchronization is asynchronous, so avoid doing it during a
time-sensitive update or draw. A file chosen through a browser file picker is
also not automatically persistent; the application must save a copy if it
needs the file after a reload.

.. note:: Files in the default in-memory VFS only exist for the current page
          session. The ``/data`` and ``/cache`` mounts created by
          ``pyglet-web`` are backed by persistent browser storage and can
          survive a refresh.

Building and serving an application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``pyglet-web`` tool packages Python sources and explicitly declared
resources, creates the Pyodide launcher, and can serve the resulting directory.

Quick start
"""""""""""

Configure a project in ``pyproject.toml``::

    [tool.pyglet.web]
    entrypoint = "game.py"
    output = "dist/web"
    sources = ["*.py", "game/**/*.py"]
    resources = ["assets", "levels/**/*.json"]
    title = "Super Game"

Each ``sources`` and ``resources`` entry may be a file, a glob, or a directory.
Directories are included recursively. Both are placed in ``application.zip``
at their project-relative paths.

Build or serve the project from a pyglet source checkout::

    python tools/web.py build
    python tools/web.py serve --open

Recommended layout
""""""""""""""""""

Keep Python code, application resources, and browser files separate::

    my-game/
    ├── pyproject.toml
    ├── main.py
    ├── game/                 # additional Python modules
    │   └── state.py
    ├── assets/               # images, audio, data, shaders
    │   ├── images/
    │   └── sounds/
    └── web/                  # HTML, CSS, JavaScript, and fonts
        ├── index.html
        ├── style.css
        └── fonts/
            └── game.woff2

``assets/`` is available to Python through the resource loader. ``web/`` is
copied directly into the browser build.

Custom page and fonts
""""""""""""""""""""""

A ``web/index.html`` replaces pyglet's default page. It must load the generated
launcher; the status element is optional but displays startup errors::

    <canvas id="pygletCanvas"></canvas>
    <pre id="pygletStatus">Loading&hellip;</pre>
    <script type="module" src="pyglet-web.js"></script>

Set ``pyglet.options.pyodide.canvas_id`` before creating a window when using a
different canvas ID. Fonts below ``web/`` can be preloaded before Python starts::

    [[tool.pyglet.web.fonts]]
    name = "Action Man"
    path = "fonts/action_man.woff2"
    weight = "400"
    style = "normal"

``name`` is the font family used by pyglet and ``path`` is relative to ``web/``.
Other string properties are passed as `FontFace descriptors
<https://developer.mozilla.org/en-US/docs/Web/API/FontFace/FontFace>`_. The
build waits for every configured font before it runs the Python entry point.

Without ``pyproject.toml``
"""""""""""""""""""""""""

Reading ``pyproject.toml`` uses the standard-library ``tomllib`` module on
Python 3.11 and newer. On Python 3.10, install the optional `tomli
<https://pypi.org/project/tomli/>`_ reader::

    python -m pip install tomli

Or pass the configuration on the command line::

    python tools/web.py --entrypoint game.py --output dist/web \
        --source game.py --source "game/**/*.py" \
        --resource assets --resource "levels/**/*.json" build

Repeat ``--source`` and ``--resource`` as needed. ``serve`` accepts the same
options, followed by server options such as ``--open``.

Checking resource declarations
""""""""""""""""""""""""""""

The optional discovery command reports literal resource calls missing from the
declared resource patterns::

    python tools/web.py discover --missing

It cannot find dynamically constructed names, so review resource declarations
after exercising dynamic loading paths.

Persistent application data
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Projects built by ``pyglet-web`` mount persistent browser storage before the
Python entry point runs. Application code can therefore use normal synchronous
filesystem operations through :mod:`pyglet.storage`::

    storage = pyglet.storage.get("super-game")
    (storage.data / "save.json").write_text(save_json, encoding="utf8")
    (storage.cache / "level-preview.png").write_bytes(preview_data)

    video = storage.settings.create(
        "video",
        defaults={"size": [1280, 720], "fullscreen": False},
    )
    video["fullscreen"] = True

    @storage.event
    def on_sync():
        print("Save complete")

    @storage.event
    def on_sync_error(error):
        print(f"Save failed: {error}")

    storage.settings.sync()

``sync`` returns immediately. Browser synchronization is asynchronous
internally, and completion is delivered through pyglet's event system rather
than requiring the application to use ``await``. Multiple calls made during an
active synchronization are combined into one follow-up pass.

Custom browser launchers
^^^^^^^^^^^^^^^^^^^^^^^^
Pyglet includes ``pyglet/libs/emscripten/pyglet_emscripten.js`` for projects
that use another web builder. Copy that file into the web project and import
its installer after loading Pyodide::

    import { installPygletEmscripten } from "./pyglet_emscripten.js";

    const pyodide = await loadPyodide();
    await installPygletEmscripten(pyodide);

The installer registers the ``pyglet_emscripten`` JavaScript module expected
by pyglet, mounts and restores ``/data`` with IDBFS, and mounts ``/cache`` with
OPFS before Python starts. ``Storage.sync`` can then persist both locations.
The ``pyglet-web`` tool copies and imports this same module automatically.

For custom paths or launchers that mount one location themselves, pass options
to the installer. A ``null`` path skips that mount::

    await installPygletEmscripten(pyodide, {
        dataPath: "/data",
        cachePath: null,
    });


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

Without optional packages, pyglet uses the browser's image decoder. It supports
PNG, BMP, JPEG, GIF, WebP, and AVIF when the active browser supports the
format. If Pillow is loaded before pyglet is imported, it takes priority and
provides Pillow's additional image formats. Pillow can also be up to five times
faster at loading images, but does add an additional dependency.

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
