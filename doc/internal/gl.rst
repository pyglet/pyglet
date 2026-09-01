OpenGL Interface Implementation
--------------------------------

See `OpenGL Interface` for details on the publicly-visible modules.

See `ctypes Wrapper Generation` for details on some of these modules are
generated.

ctypes linkage
==============

Most functions link to libGL.so (Linux), opengl32.dll (Windows) or
OpenGL.framework (OS X).  ``pyglet.graphics.api.gl.lib`` provides some helper types then
imports linker functions for the appropriate platform: one of
``pyglet.libs.darwin.lib_agl``, ``pyglet.libs.linux.glx.lib_glx``, ``pyglet.libs.win32.lib_wgl``.

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
   ``pyglet.libs``), which raises an exception.  The exception message
   details the name of the function, and optionally the name of the extension
   or OpenGL version it requires.

Binding regeneration
====================

The generated binding sources, registry extension policy, and the separate
C-header wrapper pipeline are documented in :doc:`generated`.

To access the linking function, import ``pyglet.graphics.api.gl.lib`` and use one of
``link_AGL``, ``link_GLX``, ``link_WGL`` or ``link_GL``.  This
is what the generated modules do.
