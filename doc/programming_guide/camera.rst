.. _guide_camera:

Cameras and Views
=================

Pyglet provides camera scopes in :py:mod:`pyglet.window.camera` for 2D and 3D rendering.
For common 2D workflows, use :py:class:`~pyglet.window.camera.Camera2D`. By default, the
window is created with a 2D camera.

Default camera behavior
-----------------------

Every window has a default camera at :py:attr:`pyglet.window.Window.default_camera`.
The :py:attr:`~pyglet.window.Window.projection`, :py:attr:`~pyglet.window.Window.view`,
and :py:attr:`~pyglet.window.Window.viewport` properties proxy directly to it.

The default camera is initialized with the window context creation and applies itself
automatically.

Creating a camera
-----------------

Create cameras from a window, and optionally configure scroll/zoom behavior::

    window = pyglet.window.Window()

    world_camera = pyglet.window.camera.Camera2D(
        window,
        scroll_speed=5,
        min_zoom=1,
        max_zoom=4,
    )
    gui_camera = pyglet.window.camera.Camera2D(window)

    world_camera.zoom += 0.25
    world_camera.move(1, 0)
    world_camera.position = (50, 0)


Creating views
--------------

A camera can have multiple views. Views let you scope additional transforms and scissor
areas inside one camera.

Use ``camera.create_view()`` for additional view scopes. This is useful for parallax
layers, minimaps, and nested local transforms::

    window = pyglet.window.Window()

    ui_camera = pyglet.window.camera.Camera2D(window)
    inherited_view = ui_camera.create_view(inherit=True)      # Inherits parent transform chain.
    independent_view = ui_camera.create_view(inherit=False)   # Parented to camera root view.

Views share the camera's viewport/projection behavior and can be used anywhere a camera
scope is expected.

Views can also be created from other views. For example::

    ui_camera = pyglet.window.camera.Camera2D(window)
    scroll_box_a = ui_camera.create_view()
    scroll_box_b = scroll_box_a.create_view()

If ``scroll_box_a`` moves or zooms, ``scroll_box_b`` inherits those changes.

Using camera scopes with batches
--------------------------------

Cameras can be used to target a specific batch instead of groups::

    @window.event
    def on_draw():
        window.clear()

        with world_batch.draw_with_options() as options:
            options.camera = world_camera

        with gui_batch.draw_with_options() as options:
            options.camera = gui_camera


Using camera scopes in groups
-----------------------------

Attach camera scopes to groups with ``Group.set_camera``::

    world_group = pyglet.graphics.Group(order=0)
    world_group.set_camera(world_camera)

    ui_group = pyglet.graphics.Group(order=1)
    ui_group.set_camera(window.default_camera)

    pyglet.sprite.Sprite(world_image, batch=batch, group=world_group)
    pyglet.text.Label("HUD", batch=batch, group=ui_group)


.. note:: ``Group.set_camera`` applies camera state at draw entry by calling ``begin()``.
          It does not call ``end()`` during group unsetting.

Viewport
--------

Each camera has a ``viewport`` in framebuffer coordinates::

    world_camera.viewport = (0, 0, window.width // 2, window.height)

By default, viewport follows the full framebuffer and updates on resize/scale events.
Setting a tuple makes viewport explicit, and will no longer update automatically. In those
cases you will have to update your viewport coordinates explicitly.

Scissor
-------

Scissor clipping can be set on both cameras and views.

Use ``set_scissor_area(...)`` for fixed window-space clipping::

    world_camera.set_scissor_area(0, 0, window.width // 2, window.height)

Use ``set_scissor_area_relative(...)`` when clipping should move with the
camera/view transform::

    moving_panel = ui_camera.create_view(inherit=True)
    moving_panel.set_scissor_area_relative(40, 40, 280, 160)
    moving_panel.offset_x += 16   # Scissor follows the moved view

When a camera/view is applied through ``Group.set_camera``, pyglet automatically applies
matching scissor state for that group.

For nested views, the effective scissor is the intersection of all scissor areas in the
view chain.