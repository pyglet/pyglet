pyglet.input
===============================================================

.. automodule:: pyglet.input

.. currentmodule:: pyglet.input

Classes
-------

.. autoclass:: Device
  :members:
  :undoc-members:
  :show-inheritance:

.. autoclass:: Control
  :show-inheritance:

  .. rubric:: Events

  .. automethod:: on_change

  .. rubric:: Attributes

  .. autoattribute:: value

.. autoclass:: RelativeAxis
  :members:
  :undoc-members:
  :show-inheritance:

.. autoclass:: AbsoluteAxis
  :members:
  :undoc-members:
  :show-inheritance:

.. autoclass:: Button
  :show-inheritance:

  .. rubric:: Events

  .. automethod:: on_press
  .. automethod:: on_release

  .. rubric:: Attributes

  .. autoattribute:: value

.. autoclass:: Joystick
  :show-inheritance:

  .. rubric:: Methods

  .. automethod:: open
  .. automethod:: close

  .. rubric:: Events

  .. automethod:: on_joyaxis_motion
  .. automethod:: on_joyhat_motion
  .. automethod:: on_joybutton_press
  .. automethod:: on_joybutton_release

.. autoclass:: AppleRemote
  :show-inheritance:

  .. rubric:: Methods

  .. automethod:: open
  .. automethod:: close

  .. rubric:: Events

  .. automethod:: on_button_press
  .. automethod:: on_button_release

.. autoclass:: Tablet
  :undoc-members:

Functions
---------

.. currentmodule:: pyglet.input

.. autofunction:: get_apple_remote
.. autofunction:: get_devices
.. autofunction:: get_joysticks
.. autofunction:: get_tablets

Exceptions
----------

.. autoclass:: DeviceException
  :members:
  :undoc-members:

.. autoclass:: DeviceOpenException
  :members:
  :undoc-members:

.. autoclass:: DeviceExclusiveException
  :members:
  :undoc-members: