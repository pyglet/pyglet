pyglet.app
==========

.. automodule:: pyglet.app

Classes
-------

.. autoclass:: EventLoop

  .. rubric:: Methods

  .. automethod:: run
  .. automethod:: exit
  .. automethod:: sleep

  .. rubric:: Events

  .. automethod:: on_enter
  .. automethod:: on_exit
  .. automethod:: on_window_close

  .. rubric:: Attributes

  .. autoattribute:: has_exit

  .. rubric:: Methods (internal)

  .. automethod:: enter_blocking
  .. automethod:: exit_blocking
  .. automethod:: idle

.. autoclass:: PlatformEventLoop
  :members:
  :undoc-members:

Functions
---------

.. autofunction:: run
.. autofunction:: exit

Attributes
----------

.. autodata:: event_loop

.. autodata:: platform_event_loop

.. autodata:: windows

Exceptions
----------

.. autoclass:: AppException
