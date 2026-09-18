.. _guide_gui:

Widgets and user interfaces
===========================

The :py:mod:`pyglet.gui` module provides lightweight controls and layout
containers for game menus, toolbars, settings screens, and similar interfaces.
It is not a complete desktop widget toolkit. Widgets use pyglet's normal
rendering and event systems, so they work with batches, groups, cameras, and
the application event loop.

The UI system has three main parts:

* :py:class:`~pyglet.gui.UIManager` receives input from the window, sends it to
  the appropriate widgets, and tracks keyboard focus and cursor changes.
* Widgets such as :py:class:`~pyglet.gui.TextButton` and
  :py:class:`~pyglet.gui.TextEntry` display controls and emit events when the
  user clicks them or changes their values.
* Layouts provide a new way to arrange and resize widgets and other content.

Every interactive widget must be attached to a UI manager, frame, or
scrollable region. Pass that parent to the widget constructor. The widget is
registered automatically.

.. contents::
   :local:
   :depth: 2


Quick start
-----------

Create one UI manager for a window, pass it to each top-level widget, and draw
the widgets' batch in the window's ``on_draw`` event::

    import pyglet

    window = pyglet.window.Window(640, 360)
    batch = pyglet.graphics.Batch()
    ui = pyglet.gui.UIManager(window)

    button = pyglet.gui.TextButton(
        ui,
        x=40,
        y=280,
        text="Start",
        batch=batch,
    )

    @button.event
    def on_press(widget):
        print(f"Pressed {widget.text!r}")

    @button.event
    def on_release(widget):
        print(f"Released {widget.text!r}")

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    pyglet.app.run()

The manager registers itself as a window event handler. Do not also push each
managed widget onto the window.

Set ``ui.enable = False`` to stop input routing and periodic layout updates.


Managers, parents, and focus
----------------------------

The UI manager receives window input and sends it to the appropriate widget.
Each widget has a parent that tells the manager where it belongs. Top-level
widgets use the manager as their parent, while contained widgets use their
frame or scrollable region. Layouts arrange content but do not handle input.

The manager registers its own window event handlers. Add other handlers with
``window.push_handlers`` because ``@window.event`` can replace a handler the
manager needs. For example::

    def on_resize(width, height):
        region.size = width - 80, height - 100

    window.push_handlers(on_resize=on_resize)

Text entries request focus when clicked. Applications and custom controls can
manage focus explicitly::

    ui.set_focus(text_entry)
    assert ui.focused_widget is text_entry

    ui.set_focus(None)

Widgets dispatch ``on_focus_gain`` and ``on_focus_lost`` when the manager's
focus target changes.


Widgets and their events
------------------------

The built-in controls are:

========================  ================================================
Widget                    Main events
========================  ================================================
``PushButton``            ``on_press(widget)``, ``on_release(widget)``
``TextButton``            ``on_press(widget)``, ``on_release(widget)``
``ToggleButton``          ``on_toggle(widget, value)``
``Slider``                ``on_change(widget, value)``
``TextEntry``             ``on_commit(widget, text)``
========================  ================================================

Every widget event includes the widget instance as its first argument. This
makes one handler reusable across several controls::

    def show_value(widget, value):
        print(widget, value)

    toggle_a.set_handler("on_toggle", show_value)
    toggle_b.set_handler("on_toggle", show_value)
    slider.set_handler("on_change", show_value)

Use the common :py:attr:`~pyglet.gui.WidgetBase.enabled` property to accept or
ignore input. The :py:attr:`~pyglet.gui.WidgetBase.value` property reads or
updates the control's current value without dispatching its user-input event.


Image buttons, toggles, and sliders
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Image-based controls accept textures for their visual states. Loading through
:py:func:`pyglet.resource.texture` allows pyglet to use a texture atlas::

    released = pyglet.resource.texture("button.png")
    pressed = pyglet.resource.texture("button-pressed.png")
    hover = pyglet.resource.texture("button-hover.png")

    save_button = pyglet.gui.PushButton(
        ui, 40, 220,
        pressed=pressed,
        unpressed=released,
        hover=hover,
        batch=batch,
    )

    toggle = pyglet.gui.ToggleButton(
        ui, 40, 160,
        pressed=pressed,
        unpressed=released,
        hover=hover,
        batch=batch,
    )

For a slider, provide a base image and a knob image. Values range from ``0``
to ``100``::

    slider = pyglet.gui.Slider(
        ui, 40, 100,
        base=pyglet.resource.texture("slider.png"),
        knob=pyglet.resource.texture("knob.png"),
        edge=5,
        batch=batch,
    )


Text entry
^^^^^^^^^^

A text entry retains keyboard focus after the pointer moves away. Enter or
Return dispatches ``on_commit`` and releases focus::

    name = pyglet.gui.TextEntry(
        ui,
        "Player one",
        x=40,
        y=40,
        width=220,
        batch=batch,
    )

    @name.event
    def on_commit(widget, text):
        print(f"New name: {text}")


Arranging content with layouts
------------------------------

A layout cell can contain any object with writable ``position``, ``width``,
and ``height`` attributes. This includes widgets, labels, sprites, shapes, and
nested layouts.

Use :py:class:`~pyglet.gui.HBox` and :py:class:`~pyglet.gui.VBox` for a single
row or column. Their :py:meth:`~pyglet.gui.VBox.append` and
:py:meth:`~pyglet.gui.VBox.remove` methods manage the sequence::

    menu = pyglet.gui.VBox(
        ui,
        x=40,
        y=40,
        width=220,
        height=240,
        style=pyglet.gui.LayoutStyle(
            row_size=44,
            cell_margin=(0, 8),
            cell_padding=(4, 10, 4, 10),
            cell_stretch_content=(True, True),
        ),
        batch=batch,
    )

    for caption in ("Play", "Options", "Quit"):
        button = pyglet.gui.TextButton(ui, 0, 0, caption, batch=batch)
        menu.append(button)

The widgets use ``ui`` as their parent because ``ui`` owns their input. The
``VBox`` controls their position and size. If this layout were inside a frame,
both the layout and its widgets would use that frame as their input parent.

For a grid, create a :py:class:`~pyglet.gui.Layout` with explicit rows and
columns and assign content to cells. Row zero is the top row::

    grid = pyglet.gui.Layout(
        ui, 300, 40, 300, 240,
        rows=2,
        columns=2,
        style=pyglet.gui.LayoutStyle(cell_margin=8, cell_padding=6),
        batch=batch,
    )

    label = pyglet.text.Label("Music", batch=batch)
    slider = pyglet.gui.Slider(
        ui, 0, 0,
        pyglet.resource.texture("slider.png"),
        pyglet.resource.texture("knob.png"),
        batch=batch,
    )
    grid.cell(0, 0).content = label
    grid.cell(0, 1).content = slider
    grid.set_cell_span(1, 0, colspan=2)

Cell spans begin at their top-left cell. Covered cells return ``None`` from
:py:meth:`~pyglet.gui.Layout.cell`.


Sizing, alignment, and styles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:py:class:`~pyglet.gui.LayoutStyle` supplies defaults for a layout and the
cells it creates. Useful fields include:

* ``padding``: space inside the layout as ``(top, right, bottom, left)``.
* ``cell_margin``: horizontal and vertical space between cells.
* ``cell_padding``: space inside every cell.
* ``cell_content_alignment``: horizontal and vertical alignment, such as
  ``("left", "top")``.
* ``cell_stretch_content``: one boolean or ``(horizontal, vertical)`` flags.
* ``row_size`` and ``column_size``: a pixel number, a string such as
  ``"40px"`` or ``"25%"``, or ``None`` for flexible sizing.
* ``background`` and ``cell_background``: an RGB/RGBA color or compatible
  resizable drawable.

Adjust one cell after creation with
:py:meth:`~pyglet.gui.LayoutCell.set_style`::

    grid.cell(0, 0).set_style(
        pyglet.gui.LayoutCellStyle(
            padding=(8, 12, 8, 12),
            content_alignment=("right", "center"),
        )
    )

Use ``set_row_size``, ``set_column_size``, ``set_row_margin``, and
``set_column_margin`` when individual rows or columns need different values.
``fit_to_content()`` updates a layout to its calculated cell extents.

Text buttons accept a :py:class:`~pyglet.gui.TextButtonStyle` for their
interaction colors::

    button_style = pyglet.gui.TextButtonStyle(
        unpressed_color=(230, 230, 240, 255),
        hover_color=(120, 210, 255, 255),
        pressed_color=(255, 190, 100, 255),
    )

    styled_button = pyglet.gui.TextButton(
        ui, 0, 0, "Apply", style=button_style, batch=batch
    )


Frames and nested layouts
^^^^^^^^^^^^^^^^^^^^^^^^^

A :py:class:`~pyglet.gui.Frame` is a visual grid layout and an input parent for
the widgets inside it. It is useful for a panel that should own and remove its
controls as a group::

    panel = pyglet.gui.Frame(
        ui, 40, 40, 300, 180,
        rows=3,
        columns=1,
        style=pyglet.gui.LayoutStyle(
            background=(25, 35, 55, 255),
            cell_padding=10,
            cell_stretch_content=True,
        ),
        batch=batch,
    )

    title = pyglet.text.Label("Settings", batch=batch)
    apply_button = pyglet.gui.TextButton(panel, 0, 0, "Apply", batch=batch)
    panel.cell(0, 0).content = title
    panel.cell(1, 0).content = apply_button

Nested layouts must be constructed with the layout that will contain them.
Interactive widgets inside nested layouts still use the nearest frame,
manager, or scrollable region as their parent::

    actions = pyglet.gui.HBox(panel, 0, 0, 280, 40, batch=batch)
    actions.append(pyglet.gui.TextButton(panel, 0, 0, "OK", batch=batch))
    actions.append(pyglet.gui.TextButton(panel, 0, 0, "Cancel", batch=batch))
    panel.cell(2, 0).content = actions

:py:class:`~pyglet.gui.MovableFrame` has the same layout behavior. Holding its
configured modifier while dragging moves the frame and its child widgets.


Deferred layout calculation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Layout mutations are collected by the UI manager and calculated together on
its periodic UI update. Appending many controls therefore causes one layout
pass instead of recalculating after every append. This applies to content,
dimension, span, style, size, and position changes.

Code that needs final positions immediately can force a pass for one layout::

    for button in buttons:
        menu.append(button)

    menu.realign()
    print(menu.cell(0).position)

Calling :py:meth:`~pyglet.gui.Layout.realign` also clears that layout's pending
update. Layouts without a UI manager calculate immediately because they have no
scheduled manager update.


Scrollable content
------------------

:py:class:`~pyglet.gui.ScrollableRegion` clips content with a child camera view
and translates pointer input into the scrolled coordinate system. Construct
the region with a manager or frame, construct its content layout with the
region, and use ``content_group`` for the content drawables::

    region = pyglet.gui.ScrollableRegion(
        ui, 40, 40, 300, 220,
        camera=window.camera,
        batch=batch,
        horizontal=False,
    )

    content = pyglet.gui.VBox(
        region, 40, 40, 300, 600,
        style=pyglet.gui.LayoutStyle(row_size=42, cell_margin=(0, 6)),
        batch=batch,
        group=region.content_group,
    )
    region.content = content

    for index in range(12):
        button = pyglet.gui.TextButton(
            region, 0, 0, f"Item {index + 1}",
            batch=batch,
            group=region.content_group,
        )
        content.append(button)

Mouse-wheel input scrolls enabled axes by ``scroll_step``. Applications can
also use ``set_scroll(x=..., y=...)``. Values are clamped to the content bounds.


Resizing a UI
-------------

The manager dispatches ``on_resize`` to its widgets and rebuilds its spatial
hash after all resize handlers finish. Update root layout or region bounds in a
window resize handler::

    def on_resize(width, height):
        menu.position = 24, 24
        menu.size = width - 48, height - 48

    window.push_handlers(on_resize=on_resize)

These assignments are included in the next deferred layout pass. Call
``menu.realign()`` at the end of the handler only when later code in the same
event needs the new cell geometry immediately.


Removing controls
-----------------

Remove a directly owned widget through the same object that owns it::

    ui.remove_widget(top_level_button)
    panel.remove_widget(panel_button)
    region.remove_widget(scrolled_button)

For an ``HBox`` or ``VBox``, call ``remove(content)`` or ``remove(index)`` to
remove the layout slot as well. For a grid cell, set ``cell.content = None``.


Custom widgets
--------------

Custom controls subclass :py:class:`~pyglet.gui.WidgetBase`. Pass the parent to
``WidgetBase``, finish creating the control's drawables, and call
``_register_with_parent()`` last so registration cannot observe a partially
initialized widget::

    class ColorSwatch(pyglet.gui.WidgetBase):
        def __init__(self, parent, x, y, color, batch):
            self.rectangle = pyglet.shapes.Rectangle(
                x, y, 32, 32, color=color, batch=batch
            )
            super().__init__(parent, x, y, 32, 32, cursor="hand")
            self._register_with_parent()

        def _update_position(self):
            self.rectangle.position = self.position

        def on_mouse_press(self, x, y, buttons, modifiers):
            if self.enabled and self._check_hit(x, y):
                print("Selected", self.rectangle.color)

Override ``update_groups`` when the manager's base draw order should change
groups owned by the custom widget. Override ``on_focus_gain`` and
``on_focus_lost`` when the control accepts keyboard or text input.

Complete runnable examples are available in ``examples/gui/widgets.py`` and
``examples/gui/widget_resize.py``.
