pyglet.shapes2d.collidable
==========================

.. automodule:: pyglet.shapes2d.collidable

.. autoclass:: CollisionShapeBase
  :show-inheritance:

  .. rubric:: Methods

  .. automethod:: collide

  .. rubric:: Attributes

  .. autoattribute:: x
  .. autoattribute:: y
  .. autoattribute:: position
  .. autoattribute:: anchor_x
  .. autoattribute:: anchor_y
  .. autoattribute:: anchor_position
  .. autoattribute:: rotation

  .. rubric:: Events

  .. automethod:: on_enter
  .. automethod:: on_collide
  .. automethod:: on_leave


.. autoclass:: CollisionCircle
  :show-inheritance:

  .. autoattribute:: radius


.. autoclass:: CollisionEllipse
  :show-inheritance:

  .. autoattribute:: a
  .. autoattribute:: b


.. autoclass:: CollisionRectangle
  :show-inheritance:

  .. autoattribute:: width
  .. autoattribute:: height


.. autoclass:: CollisionSector
  :show-inheritance:

  .. autoattribute:: radius
  .. autoattribute:: angle
  .. autoattribute:: start_angle


.. autoclass:: CollisionPolygon
  :show-inheritance:

  .. autoattribute:: coordinates
