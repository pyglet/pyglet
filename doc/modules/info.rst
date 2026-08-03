.. _pyglet-info:

pyglet.info
===========

``pyglet.info`` records system, driver, and active graphics-context details
for bug reports::

    python -m pyglet.info > info.txt

Use the isolated graphics probe to test the OpenGL and OpenGL ES versions
supported by pyglet on that machine. It also compiles pyglet's built-in
startup shaders for each successful context::

    python -m pyglet.info --probe-graphics > info.txt

Test one specific request with ``--backend`` and ``--version``::

    python -m pyglet.info --backend gles3 --version 3.1

Command-line options
--------------------

``python -m pyglet.info`` accepts the following public options:

.. list-table::
   :header-rows: 1

   * - Option
     - Purpose
   * - ``-h``, ``--help``
     - Show the command-line help text.
   * - ``-extensions``
     - Include complete graphics and audio extension lists instead of shortened previews.
   * - ``--verbose``
     - Include full tracebacks when a diagnostic section fails.
   * - ``--backend BACKEND``
     - Use ``opengl``, ``gl2``, ``gles3``, ``gles2``, ``webgl``, or ``vulkan`` for the main report.
   * - ``--version MAJOR.MINOR``
     - Explicitly request an OpenGL or OpenGL ES version for the main report. Requires ``--backend``; omit it to use the backend's default version.
   * - ``--probe-graphics``
     - Test pyglet's supported OpenGL-family requests in isolated processes and print a recommendation.

The ``--graphics-worker`` option is reserved for the probe's internal subprocesses and is not part of the public CLI.

.. automodule:: pyglet.info
  :members:
  :undoc-members:
