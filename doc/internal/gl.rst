OpenGL Interface Implementation
--------------------------------

See `OpenGL Interface` for details on the publically-visible modules.

See `ctypes Wrapper Generation` for details on some of these modules are
generated.

ctypes linkage
==============

Most functions link to libGL.so (Linux), opengl32.dll (Windows) or
OpenGL.framework (OS X).  ``pyglet.gl.lib`` provides some helper types then
imports linker functions for the appropriate platform: one of
``pyglet.gl.lib_agl``, ``pyglet.gl.lib_glx``, ``pyglet.gl.lib_wgl``.

On any platform, the following steps are taken to link each function during
import:

1. Look in the appropriate library (e.g. libGL.so, opengl32.dll,
   etc.) using ``cdll`` or ``windll``.

2. If not found, call ``wglGetProcAddress`` or ``glxGetProcAddress`` to try to
   resolve the function's address dynamically.  On OS X, skip this step.

3. On Windows, this will fail if the context hasn't been created yet.  Create
   and return a proxy object ``WGLFunctionProxy`` which will try the same
   resolution again when the object is ``__call__``'d.

   The proxy object caches its result so that subsequent calls have only a
   single extra function-call overhead.

4. If the function is still not found (either during import or proxy call),
   the function is replaced with ``MissingFunction`` (defined in
   ``pyglet.gl.lib``), which raises an exception.  The exception message
   details the name of the function, and optionally the name of the extension
   or OpenGL version it requires.

   We currently include all functions and enums from OpenGL 4.6 in separate
   modules. ``gl.g`` exposes the core api and ``gl_compat.py`` exposes the
   compatibility profile (no deprecation).

   What extensions are included can be found in ``gengl.py``.

To access the linking function, import ``pyglet.gl.lib`` and use one of
``link_AGL``, ``link_GLX``, ``link_WGL`` or ``link_GL``.  This
is what the generated modules do.

Missing extensions
==================

Missing extensions can be added to the ``extensions`` list in ``gengl.py``.
