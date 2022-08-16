pyglet.media
============

.. rubric:: Submodules

.. toctree::
   :maxdepth: 1

   media_synthesis

.. rubric:: Details

.. currentmodule:: pyglet.media

.. automodule:: pyglet.media

Classes
-------

.. autoclass:: pyglet.media.player.Player
  :members: loop

  .. rubric:: Methods

  .. automethod:: play
  .. automethod:: pause
  .. automethod:: queue
  .. automethod:: seek
  .. automethod:: seek_next_frame
  .. automethod:: get_texture
  .. automethod:: next_source
  .. automethod:: delete
  .. automethod:: update_texture

  .. rubric:: Events

  .. automethod:: on_eos
  .. automethod:: on_player_eos
  .. automethod:: on_player_next_source

  .. rubric:: Attributes

  .. autoattribute:: cone_inner_angle
  .. autoattribute:: cone_outer_angle
  .. autoattribute:: cone_orientation
  .. autoattribute:: cone_outer_gain
  .. autoattribute:: min_distance
  .. autoattribute:: max_distance
  .. autoattribute:: pitch
  .. autoattribute:: playing
  .. autoattribute:: position
  .. autoattribute:: source
  .. autoattribute:: texture
  .. autoattribute:: time
  .. autoattribute:: volume

.. autoclass:: pyglet.media.player.PlayerGroup

  .. automethod:: play
  .. automethod:: pause

.. autoclass:: pyglet.media.codecs.AudioFormat
.. autoclass:: pyglet.media.codecs.VideoFormat
.. autoclass:: pyglet.media.codecs.AudioData
    :members:

.. autoclass:: pyglet.media.codecs.SourceInfo
    :members:

.. autoclass:: Source
  :members:

.. autoclass:: StreamingSource
  :members:
  :undoc-members:
  :show-inheritance:

.. autoclass:: StaticSource
  :members:
  :undoc-members:
  :show-inheritance:

.. autoclass:: pyglet.media.codecs.StaticMemorySource
  :members:
  :undoc-members:
  :show-inheritance:

.. autoclass:: pyglet.media.drivers.listener.AbstractListener
  :members:
  :undoc-members:

.. autoclass:: pyglet.media.drivers.base.MediaEvent
    :members:

Functions
---------

.. autofunction:: get_audio_driver
.. autofunction:: load
.. autofunction:: have_ffmpeg

Exceptions
----------

.. automodule:: pyglet.media.exceptions
  :members:
  :undoc-members:
