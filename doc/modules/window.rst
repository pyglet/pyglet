pyglet.window
=============

.. rubric:: Submodules

.. toctree::
   :maxdepth: 1

   window_key
   window_mouse

.. rubric:: Details

.. automodule:: pyglet.window

Classes
-------

.. autoclass:: Window
  :show-inheritance:

  .. rubric:: Methods

  .. automethod:: activate
  .. automethod:: clear
  .. automethod:: close
  .. automethod:: dispatch_event
  .. automethod:: dispatch_events
  .. automethod:: draw_mouse_cursor
  .. automethod:: flip
  .. automethod:: get_location
  .. automethod:: get_size
  .. automethod:: get_system_mouse_cursor
  .. automethod:: maximize
  .. automethod:: minimize
  .. automethod:: set_caption
  .. automethod:: set_exclusive_keyboard
  .. automethod:: set_exclusive_mouse
  .. automethod:: set_fullscreen
  .. automethod:: set_icon
  .. automethod:: set_location
  .. automethod:: set_maximum_size
  .. automethod:: set_minimum_size
  .. automethod:: set_mouse_cursor
  .. automethod:: set_mouse_platform_visible
  .. automethod:: set_mouse_visible
  .. automethod:: set_size
  .. automethod:: set_visible
  .. automethod:: switch_to

  .. rubric:: Events

  .. automethod:: on_activate
  .. automethod:: on_close
  .. automethod:: on_context_lost
  .. automethod:: on_context_state_lost
  .. automethod:: on_deactivate
  .. automethod:: on_draw
  .. automethod:: on_expose
  .. automethod:: on_hide
  .. automethod:: on_key_press
  .. automethod:: on_key_release
  .. automethod:: on_mouse_drag
  .. automethod:: on_mouse_enter
  .. automethod:: on_mouse_leave
  .. automethod:: on_mouse_motion
  .. automethod:: on_mouse_press
  .. automethod:: on_mouse_release
  .. automethod:: on_mouse_scroll
  .. automethod:: on_move
  .. automethod:: on_resize
  .. automethod:: on_show
  .. automethod:: on_text
  .. automethod:: on_text_motion
  .. automethod:: on_text_motion_select

  .. rubric:: Attributes

  .. autoattribute:: caption
  .. autoattribute:: config
  .. autoattribute:: context
  .. autoattribute:: display
  .. autoattribute:: fullscreen
  .. autoattribute:: has_exit
  .. autoattribute:: height
  .. autoattribute:: invalid
  .. autoattribute:: resizeable
  .. autoattribute:: screen
  .. autoattribute:: style
  .. autoattribute:: visible
  .. autoattribute:: vsync
  .. autoattribute:: width

  .. rubric:: Class attributes: cursor names

  .. autoattribute:: CURSOR_CROSSHAIR
  .. autoattribute:: CURSOR_DEFAULT
  .. autoattribute:: CURSOR_HAND
  .. autoattribute:: CURSOR_HELP
  .. autoattribute:: CURSOR_NO
  .. autoattribute:: CURSOR_SIZE
  .. autoattribute:: CURSOR_SIZE_DOWN
  .. autoattribute:: CURSOR_SIZE_DOWN_LEFT
  .. autoattribute:: CURSOR_SIZE_DOWN_RIGHT
  .. autoattribute:: CURSOR_SIZE_LEFT
  .. autoattribute:: CURSOR_SIZE_LEFT_RIGHT
  .. autoattribute:: CURSOR_SIZE_RIGHT
  .. autoattribute:: CURSOR_SIZE_UP
  .. autoattribute:: CURSOR_SIZE_UP_DOWN
  .. autoattribute:: CURSOR_SIZE_UP_LEFT
  .. autoattribute:: CURSOR_SIZE_UP_RIGHT
  .. autoattribute:: CURSOR_TEXT
  .. autoattribute:: CURSOR_WAIT
  .. autoattribute:: CURSOR_WAIT_ARROW

  .. rubric:: Class attributes: window styles

  .. autoattribute:: WINDOW_STYLE_BORDERLESS
  .. autoattribute:: WINDOW_STYLE_DEFAULT
  .. autoattribute:: WINDOW_STYLE_DIALOG
  .. autoattribute:: WINDOW_STYLE_TOOL


.. autoclass:: FPSDisplay
  :members:
  :undoc-members:
  :show-inheritance:

.. autoclass:: MouseCursor
  :members:
  :undoc-members:

.. autoclass:: DefaultMouseCursor
  :show-inheritance:

.. autoclass:: ImageMouseCursor
  :members:
  :undoc-members:
  :show-inheritance:


Exceptions
----------

.. autoclass:: MouseCursorException
.. autoclass:: NoSuchConfigException
.. autoclass:: NoSuchDisplayException
.. autoclass:: WindowException
