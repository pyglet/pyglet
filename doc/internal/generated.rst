ctypes Wrapper Generation
=========================

Pyglet has two ctypes-generation processes. The OpenGL-family
bindings use Khronos XML registries. The remaining legacy wrappers parse local
C headers.

Khronos XML registry bindings
-----------------------------

The XML registry generators live in ``tools/gen_opengl``:

* ``gengl.py`` generates OpenGL core, compatibility, and OpenGL ES bindings
  from ``gl.xml``.
* ``gen_egl.py``, ``gen_glx.py``, and ``gen_wgl.py`` generate the EGL, GLX,
  and WGL bindings from ``egl.xml``, ``glx.xml``, and ``wgl.xml``.
* There is no agl.xml file available, and is therefore no longer generated.
  Since AGL is deprecated, it will not require any future updates.

Run the generators from the repository root::

    python tools/gen_opengl/gengl.py --source local
    python tools/gen_opengl/gen_egl.py
    python tools/gen_opengl/gen_glx.py
    python tools/gen_opengl/gen_wgl.py

``gengl.py`` can also retrieve the current ``gl.xml`` with ``--source url``.
The generated OpenGL modules are ``pyglet.graphics.api.gl.gl``,
``pyglet.graphics.api.gl.gl_compat``, and ``pyglet.graphics.api.gl.gles``.

Extension bindings
------------------

Each generator has an ``EXTENSIONS`` list. It contains extensions pyglet uses
or that are common enough for the normal binding module. The
registry contains many legacy and vendor specific extensions, so generating all
of them by default would substantially increase module size, increase time
spent linking/importing, and may require additional platform specific ctypes
declarations.

EGL, GLX, and WGL can write selected extensions to a sibling ``*_ext.py``
module instead::

    python tools/gen_opengl/gen_egl.py --extensions-file
    python tools/gen_opengl/gen_glx.py --extensions-file
    python tools/gen_opengl/gen_wgl.py --extensions-file

Use ``--extra-extensions`` with ``--extensions-file`` to generate all unlisted
registry extensions into that extra module. Add any required type mappings and
template imports before enabling an extension that uses platform specific
types.

If an extension is useful to pyglet and broadly supported, add it to the
relevant ``EXTENSIONS`` list. For experimental, legacy, or application specific
extensions, prefer separate extension output.

If there is a commonly used extension, or your application relies on a specific
extension that pyglet does not include by default, we can include it. Feel free
to open an issue or pull request with the specific extension.

C-header wrapper bindings
-------------------------

``tools/genwrappers.py`` invokes the ``tools/wraptypes`` preprocessor
and C parser over headers installed on the local system. Unlike the XML
generators, it is platform and development header dependent. It is used for
X11 and a small number of other platform libraries, not EGL, GLX, or WGL.

On Linux, request the wrappers to generate explicitly::

    python tools/genwrappers.py xlib xinerama

This requires the corresponding X11 and Xinerama development headers. The
current script still contains output paths from the former X11 package layout;
update those paths before regenerating the relocated
``pyglet.libs.linux.x11`` modules.
