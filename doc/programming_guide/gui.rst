.. _guide_gui:

Simple Widgets & GUI
====================

The :py:mod:`pyglet.gui` module provides a limited selection of widgets, that can
be used to add user interface elements to your game or application. The selection
is limited, but will cover the most common use cases. For example: the configuration
screen in a game, or a set of toolbar buttons for a visualization program.

Widgets are internally quite simple in design, being constructed from other high
level pyglet objects. For instance, widgets are event handlers that receive keyboard
and mouse events from the Window. They can then in turn dispatch their own custom
events, because they subclass :py:class:`~pyglet.event.EventDispatcher`. In order to
understand how this all works, you should read through the :ref:`guide_events`
section of the documentation.


Creating a Widget
-----------------
TBD


Frame objects
-------------
TBD
