Runtime Options
===============

Pyglet offers a way to change runtime behavior through options. These options provide ways to modify specific modules, behavior for specific operating systems, or adding more debugging information. Options can be specified as a key, or as an attribute with the ``pyglet.options`` dataclass instance.

To change an option from its default, you must import ``pyglet`` before any sub-packages.

For example::

  import pyglet
  pyglet.options['debug_gl'] = False
  pyglet.options.debug_media = True

The default options can be overridden from the OS environment as well.  The
corresponding environment variable for each option key is prefaced by
``PYGLET_``.  For example, in Bash you can set the ``debug_gl`` option with::

  PYGLET_DEBUG_GL=True; export PYGLET_DEBUG_GL

For options requiring a tuple of values, separate each value with a comma.

.. autoclass:: pyglet.Options
  :members:
  :exclude-members: __init__, __new__

.. autodata:: pyglet.options

.. _guide_environment-settings:

Environment settings
--------------------

Options in the :py:attr:`pyglet.options` dictionary can have defaults set
through the operating system's environment variable.  The following table
shows which environment variable is used for each option:

    .. list-table::
        :header-rows: 1

        * - Environment variable
          - :py:attr:`pyglet.options` key
          - Type
          - Default value
        * - ``PYGLET_AUDIO``
          - ``audio``
          - List of strings
          - ``directsound,openal,alsa,silent``
        * - ``PYGLET_DEBUG_GL``
          - ``debug_gl``
          - Boolean
          - ``1`` [#debug_gl]_

.. [#debug_gl] Defaults to ``1`` unless Python is run with ``-O`` or from a
    frozen executable.
