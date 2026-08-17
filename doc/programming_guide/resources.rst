.. _guide_resources:

Application resources
=====================

Previous sections in this guide have described how to load images, media and
text documents using pyglet.  Applications also usually have the need to load
other data files: for example, level descriptions in a game, internationalised
strings, and so on.

Programmers are often tempted to load, for example, a texture required by
their application with::

    texture = pyglet.image.load('logo.png').get_texture()

This code assumes ``logo.png`` is in the current working directory.
Unfortunately the working directory is not necessarily the same as the
directory containing the application script files.

* Applications started from the command line can start from an arbitrary
  working directory.
* Applications bundled into an egg, Mac OS X package or Windows executable
  may have their resources inside a ZIP file.
* The application might need to change the working directory in order to
  work with the user's files.

A common workaround for this is to construct a path relative to the script
file instead of the working directory::

    import os

    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, 'logo.png')
    texture = pyglet.image.load(path).get_texture()

This, besides being tedious to write, still does not work for resources within
ZIP files, and can be troublesome in projects that span multiple packages.

The :py:mod:`pyglet.resource` module solves this problem elegantly::

    texture = pyglet.resource.texture('logo.png')

The following sections describe exactly how the resources are located, and how
the behaviour can be customised.

Loading resources
-----------------

Use the :py:mod:`pyglet.resource` module when files shipped with the
application need to be loaded.  For example, instead of writing::

    data_file = open('file.txt')

use::

    data_file = pyglet.resource.file('file.txt')

There are also convenience functions for loading media files for pyglet.  The
following table shows the equivalent resource functions for the standard file
functions.

    .. list-table::
        :header-rows: 1

        * - File function
          - Resource function
          - Type
        * - ``open``
          - :py:func:`pyglet.resource.file`
          - File-like object
        * - :py:func:`pyglet.image.load`
          - :py:func:`pyglet.resource.image`
          - :py:class:`~pyglet.image.ImageData`
        * - :py:func:`pyglet.image.load` followed by
            :py:meth:`~pyglet.image.ImageData.get_texture`
          - :py:func:`pyglet.resource.texture`
          - :py:class:`~pyglet.graphics.texture.Texture` or
            :py:class:`~pyglet.graphics.texture.TextureRegion`
        * - :py:func:`pyglet.image.load_animation`
          - :py:func:`pyglet.resource.animation`
          - :py:class:`~pyglet.image.animation.Animation`
        * - :py:func:`pyglet.media.load_audio`
          - :py:func:`pyglet.resource.audio`
          - :py:class:`~pyglet.media.Source`
        * - :py:func:`pyglet.media.load_video`
          - :py:func:`pyglet.resource.video`
          - :py:class:`~pyglet.media.Source`
        * - | :py:func:`pyglet.text.load`
            | mimetype = ``text/plain``
          - :py:func:`pyglet.resource.text`
          - :py:class:`~pyglet.text.document.UnformattedDocument`
        * - | :py:func:`pyglet.text.load`
            | mimetype = ``text/html``
          - :py:func:`pyglet.resource.html`
          - :py:class:`~pyglet.text.document.FormattedDocument`
        * - | :py:func:`pyglet.text.load`
            | mimetype = ``text/vnd.pyglet-attributed``
          - :py:func:`pyglet.resource.attributed`
          - :py:class:`~pyglet.text.document.FormattedDocument`
        * - :py:func:`pyglet.font.add_file`
          - :py:func:`pyglet.resource.add_font`
          - ``None``

:py:func:`pyglet.resource.texture` loads GPU-backed data for drawing. By
default, the resource module attempts to pack small textures into larger
texture atlases (explained in :ref:`guide_texture-bins-and-atlases`) for more
efficient rendering. This is why the return type can be either
:py:class:`~pyglet.graphics.texture.Texture` or
:py:class:`~pyglet.graphics.texture.TextureRegion`. Pass ``atlas=False`` when
you specifically need a stand-alone texture, such as for texture wrapping or
lower-level rendering.

:py:func:`pyglet.resource.image` loads and caches CPU-side
:py:class:`~pyglet.image.ImageData`. Use it when you need to inspect or modify
pixels before uploading them to the GPU. Although image data can be passed to
a sprite and uploaded automatically, :py:func:`pyglet.resource.texture` is the
preferred path when the asset is loaded for drawing.


Resource locations
^^^^^^^^^^^^^^^^^^

Some resource files reference other files by name.  For example, an HTML
document can contain ``<img src="image.png" />`` elements.  In this case your
application needs to locate ``image.png`` relative to the original HTML file.

Use :py:func:`pyglet.resource.location` to get a
:py:class:`~pyglet.resource.Location` object describing the location of an
application resource.  This location might be a file system
directory or a directory within a ZIP file.
The :py:class:`~pyglet.resource.Location` object can directly open files by
name, so your application does not need to distinguish between these cases.

In the following example, a ``thumbnails.txt`` file is assumed to contain a
list of image filenames (one per line), which are then loaded assuming the
image files are located in the same directory as the ``thumbnails.txt`` file::

    thumbnails_file = pyglet.resource.file('thumbnails.txt', 'rt')
    thumbnails_location = pyglet.resource.location('thumbnails.txt')

    for line in thumbnails_file:
        filename = line.strip()
        image_file = thumbnails_location.open(filename)
        image = pyglet.image.load(filename, file=image_file)
        # Do something with `image`...

This code correctly ignores other images with the same filename that might
appear elsewhere on the resource path.

Specifying the resource path
----------------------------

By default, only the script home directory is searched (the directory
containing the ``__main__`` module).
You can set :py:attr:`pyglet.resource.path` to a list of locations to
search in order.  This list is indexed, so after modifying it you will
need to call :py:func:`pyglet.resource.reindex`.

Each item in the path list is either a path relative to the script home, or
the name of a Python module preceded with an "at" symbol (``@``).  For example,
if you would like to package all your resources in a ``res`` directory::

    pyglet.resource.path = ['res']
    pyglet.resource.reindex()

Items on the path are not searched recursively, so if your resource directory
itself has subdirectories, these need to be specified explicitly::

    pyglet.resource.path = ['res', 'res/images', 'res/sounds', 'res/fonts']
    pyglet.resource.reindex()

The entries in the resource path always use forward slash characters as path
separators even when the operating systems using a different character.

Specifying module names makes it easy to group code with its resources.  The
following example uses the directory containing the hypothetical
``gui.skins.default`` for resources::

    pyglet.resource.path = ['@gui.skins.default', '.']
    pyglet.resource.reindex()

Multiple loaders
----------------

A :py:class:`~pyglet.resource.Loader` encapsulates a complete resource path
and cache.  This lets your application cleanly separate resource loading of
different modules.
Loaders are constructed for a given search path, andnexposes the same methods
as the global :py:mod:`pyglet.resource` module functions.

For example, if a module needs to load its own graphics but does not want to
interfere with the rest of the application's resource loading, it would create
its own :py:class:`~pyglet.resource.Loader` with a local search path::

    loader = pyglet.resource.Loader(['@' + __name__])
    image = loader.image('logo.png')

This is particularly suitable for "plugin" modules.

You can also use a :py:class:`~pyglet.resource.Loader` instance to load a set
of resources relative to some user-specified document directory.
The following example creates a loader for a directory specified on the
command line::

    import sys
    home = sys.argv[1]
    loader = pyglet.resource.Loader(script_home=[home])

This is the only way that absolute directories and resources not bundled with
an application should be used with :py:mod:`pyglet.resource`.

Saving user preferences and data
--------------------------------

New applications should use :mod:`pyglet.storage` for application-created
files. The older path functions documented below remain available for
compatibility.

Creating application storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Call :func:`pyglet.storage.get` with a stable application name. Repeated calls
with the same name return the same storage object::

    storage = pyglet.storage.get('SuperGame')

The name determines where pyglet stores the application's files, so it should
not change between releases. Pyglet creates each storage directory when the
object is first created.

Choosing a storage location
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The storage object separates disposable files, re-creatable caches,
application data, and settings:

.. list-table:: Storage locations
   :header-rows: 1
   :widths: 18 35 24 23

   * - Location
     - Use for
     - Desktop backing
     - Browser backing
   * - ``storage.temporary``
     - Disposable working files: downloads, intermediate files, and temporary
       exports. Do not store anything needed by a later run here.
     - Operating-system temporary directory. The OS may clean it.
     - In-memory VFS under ``/tmp``. Lost when the page reloads; it is never
       synchronized.
   * - ``storage.cache``
     - Re-creatable files that should normally survive between runs, such as
       generated previews or downloaded content. The application must work if
       these files are purged.
     - A ``cache`` directory below the application's data directory.
     - Persistent OPFS directory under ``/cache/<name>``. Call ``sync`` after
       writing files that should survive a reload.
   * - ``storage.data``
     - Persistent application content: save games, profiles, imported data,
       and content the application owns.
     - Platform application-data directory.
     - Persistent IDBFS mount under ``/data/<name>``. Call ``sync`` after an
       important write.
   * - ``storage.settings``
     - Structured configuration such as preferences, key bindings, and window
       state. It also provides access to the underlying settings directory.
     - Platform configuration directory. It may be the same physical
       directory as application data on some platforms.
     - Persistent IDBFS directory under ``/data/<name>/settings``. Call
       ``sync`` after an important write.

Writing application files
^^^^^^^^^^^^^^^^^^^^^^^^^

Each location is path-like and works with normal Python filesystem APIs. Save
games and other application-owned content normally belong in ``data``::

    save_file = storage.data / 'highscores.txt'
    save_file.write_text('10000', encoding='utf8')

Use ``temporary`` for files that can disappear at any time and ``cache`` for
files that the application can recreate. Files that belong beside structured
configuration can be written directly through ``settings``::

    controls_file = storage.settings / 'controls.ini'
    controls_file.write_text('jump=space', encoding='utf8')

Structured settings
^^^^^^^^^^^^^^^^^^^

The settings manager stores named sections together in one JSON file. Calling
:meth:`~pyglet.storage.Settings.create` gets an existing section or creates it
when it does not exist::

    window = storage.settings.create(
        'window',
        defaults={'size': [1280, 720], 'fullscreen': False},
    )

    window['fullscreen'] = True

``defaults`` only fills missing keys. It does not overwrite values loaded from
an earlier run. Assign a key to replace one value::

    window['size'] = [1920, 1080]

To replace the entire section, clear it before adding the new values::

    window.clear()
    window.update({'size': [1920, 1080], 'fullscreen': True})

Use :meth:`~pyglet.storage.Settings.remove` to delete a section completely.
Settings values must be JSON serializable; JSON arrays are returned as Python
lists.

Persisting changes
^^^^^^^^^^^^^^^^^^

Synchronize after changing settings to write every section to
``settings.json``::

    storage.settings.sync()

On ordinary desktop filesystems the write is complete when ``write_text``
returns. Browser applications use the same synchronous Python file APIs, but
must synchronize the virtual filesystem with persistent browser storage. This
does not require an ``asyncio`` application::

    @storage.event
    def on_sync():
        print('Save is persistent')

    @storage.event
    def on_sync_error(error):
        print(f'Could not persist save: {error}')

    storage.sync()

If :meth:`~pyglet.storage.Storage.sync` is called while synchronization is in
progress, pyglet coalesces the requests into one follow-up operation. The
``on_sync`` event is dispatched only after all requests made so far are
complete.

Legacy storage paths
^^^^^^^^^^^^^^^^^^^^

Because Python applications can be distributed in several ways, including
within ZIP files, it is usually not feasible to save user preferences, high
score lists, and so on within the application directory (or worse, the working
directory). The resource module provides functions for assisting with this.

The :py:func:`pyglet.resource.get_settings_path` function returns a directory
suitable for writing configuration related data. The directory used follows
the operating system's convention:

* ``~/.config/ApplicationName/`` on Linux (depends on `XDG_CONFIG_HOME` environment variable).
* ``$HOME\Application Settings\ApplicationName`` on Windows
* ``~/Library/Application Support/ApplicationName`` on Mac OS X

The :py:func:`pyglet.resource.get_data_path` function returns a directory
suitable for writing arbitrary data, such as save files. The directory used follows
the operating system's convention:

* ``~/.local/share/ApplicationName/`` on Linux (depends on `XDG_DATA_HOME` environment variable).
* ``$HOME\Application Settings\ApplicationName`` on Windows
* ``~/Library/Application Support/ApplicationName`` on Mac OS X

The returned directory names are not guaranteed to exist -- it is the
application's responsibility to create them.  The following example opens a high
score list file for a game called "SuperGame" into the data directory::

    import os

    dir = pyglet.resource.get_data_path('SuperGame')
    if not os.path.exists(dir):
        os.makedirs(dir)
    filename = os.path.join(dir, 'highscores.txt')
    file = open(filename, 'wt')
