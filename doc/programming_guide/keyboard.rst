.. _guide_keyboard-input:

Keyboard input
==============

pyglet provides multiple types of keyboard input abstraction:

#. Cross-platform key press/release events suitable for game controls
#. Unicode text entry with automatic locale and platform handling
#. Cross-platform detection of common text editing actions


All of them have the following restrictions:

#. There must be at least one pyglet :py:class:`~pyglet.window.Window`
   instance which can hold keyboard focus

#. Windows created with the following styles cannot hold keyboard focus:

   * :py:attr:`~pyglet.window.Window.WINDOW_STYLE_BORDERLESS`
   * :py:attr:`~pyglet.window.Window.WINDOW_STYLE_TOOL`


If your project's requirements fall outside these restrictions, you
should consider alternatives. Examples include:

* Python's built-in :py:func:`input` function
* The `Textual <https://www.textualize.io/projects/#textual>`_ terminal UI
  framework


Keyboard Focus Conventions
--------------------------

Keyboard focus is where the user's keyboard input is sent.

Desktop operating systems often follow these conventions:

#. Only one window can have focus
#. Clicking a window gives it focus
#. The window with focus is displayed above all others
#. The window with focus has a distinct title bar style
#. Windows can have focus taken away
#. Windows can request focus

However, the items above are not guaranteed to be true.

For example, pyglet allows you to request focus from the OS by calling
:py:meth:`Window.activate <pyglet.window.Window.activate>`. However,
the OS may not support the feature. Even if it does support it, the OS
may not only refuse, but do so without notifying the user focus was
requested.

Deviations from the conventions can occur for any of the following
reasons:

.. list-table::
   :header-rows: 1

   * - Cause
     - Example(s)

   * - Modal dialogs
     - Permission requests and error notifications

   * - User settings
     - Window focus is set to follow the mouse

   * - Platform quirks
     - Split screen utilities and Linux window managers
       with multi-focus modes


Keyboard events
---------------

The :py:meth:`~pyglet.window.Window.on_key_press` and
:py:meth:`~pyglet.window.Window.on_key_release` events are fired when
any key on the keyboard is pressed or released, respectively.  These events
are not affected by "key repeat" -- once a key is pressed there are no more
events for that key until it is released.

Both events are parameterised by the same arguments::

    def on_key_press(symbol, modifiers):
        pass

    def on_key_release(symbol, modifiers):
        pass

Defined key symbols
^^^^^^^^^^^^^^^^^^^

The `symbol` argument is an integer that represents a "virtual" key code.
It does *not* correspond to any particular numbering scheme; in particular
the symbol is *not* an ASCII character code.

pyglet has key symbols that are hardware and platform independent
for many types of keyboard.  These are defined in
:py:mod:`pyglet.window.key` as constants.  For example, the Latin-1
alphabet is simply the letter itself::

    key.A
    key.B
    key.C
    ...

The numeric keys have an underscore to make them valid identifiers::

    key._1
    key._2
    key._3
    ...

Various control and directional keys are identified by name::

    key.ENTER or key.RETURN
    key.SPACE
    key.BACKSPACE
    key.DELETE
    key.MINUS
    key.EQUAL
    key.BACKSLASH

    key.LEFT
    key.RIGHT
    key.UP
    key.DOWN
    key.HOME
    key.END
    key.PAGEUP
    key.PAGEDOWN

    key.F1
    key.F2
    ...

Keys on the number pad have separate symbols::

    key.NUM_1
    key.NUM_2
    ...
    key.NUM_EQUAL
    key.NUM_DIVIDE
    key.NUM_MULTIPLY
    key.NUM_SUBTRACT
    key.NUM_ADD
    key.NUM_DECIMAL
    key.NUM_ENTER

Some modifier keys have separate symbols for their left and right sides
(however they cannot all be distinguished on all platforms, including Mac OSX)::

    key.LCTRL
    key.RCTRL
    key.LSHIFT
    key.RSHIFT
    ...

Key symbols are independent of any modifiers being active.  For example,
lower-case and upper-case letters both generate the `A` symbol.  This is also
true of the number keypad.

Modifiers
^^^^^^^^^

The modifiers that are active when the event is generated are combined in a
bitwise fashion and provided in the ``modifiers`` parameter.  The modifier
constants defined in :py:mod:`pyglet.window.key` are::

    MOD_SHIFT
    MOD_CTRL
    MOD_ALT         Not available on Mac OS X
    MOD_WINDOWS     Available on Windows only
    MOD_COMMAND     Available on Mac OS X only
    MOD_OPTION      Available on Mac OS X only
    MOD_CAPSLOCK
    MOD_NUMLOCK
    MOD_SCROLLLOCK
    MOD_ACCEL       Equivalent to MOD_CTRL, or MOD_COMMAND on Mac OS X.

For example, to test if the shift key is held down::

    if modifiers & MOD_SHIFT:
        pass

Unlike the corresponding key symbols, it is not possible to determine whether
the left or right modifier is held down (though you could emulate this
behaviour by keeping track of the key states yourself).

User-defined key symbols
^^^^^^^^^^^^^^^^^^^^^^^^

pyglet does not define key symbols for every keyboard ever made.  For example,
non-Latin languages will have many keys not recognised by pyglet (however,
their Unicode representations will still be valid, see
:ref:`guide_text-and-motion-events`).
Even English keyboards often have additional so-called "OEM" keys
added by the manufacturer, which might be labelled "Media", "Volume" or
"Shopping", for example.

In these cases pyglet will create a key symbol at runtime based on the
hardware scancode of the key.  This is guaranteed to be unique for that model
of keyboard, but may not be consistent across other keyboards with the same
labelled key.

The best way to use these keys is to record what the user presses after a
prompt, and then check for that same key symbol.  Many commercial games have
similar functionality in allowing players to set up their own key bindings.

Remembering key state
^^^^^^^^^^^^^^^^^^^^^

:py:class:`~pyglet.window.key.KeyStateHandler` is a convenience class which
stores the current keyboard state.  Instances can be pushed onto the event
handler stack of any window and subsequently queried using key code constants
as keys::

    from pyglet.window import key

    window = pyglet.window.Window()
    keys = key.KeyStateHandler()
    window.push_handlers(keys)

    # Check if the spacebar is currently pressed:
    if keys[key.SPACE]:
        pass

.. _guide_text-and-motion-events:

Text Input and Motion Events
----------------------------

pyglet offers Unicode text input events in addition to individual key events.
There are several benefits to this:

* Automatic and correct mapping of platform-specific modifiers and key symbols
  to Unicode characters
* Key repeat for held keys is automatically applied to text input according to
  the user's operating system preferences.
* Dead keys and compose keys are automatically interpreted to produce
  diacritic marks or combining characters.
* Keyboard input can be routed via an input palette, for example to input
  characters from Asian languages.
* Text input can come from other user-defined sources, such as handwriting or
  voice recognition.

The actual source of input (i.e., which keys were pressed, or what input
method was used) should be considered outside of the scope of the application
-- the operating system provides the necessary services.

When text is entered into a window, the
:py:meth:`~pyglet.window.Window.on_text` event is fired::

    def on_text(text):
        pass

The only parameter provided is a Unicode string.
Although this will usually be one character long for direct keyboard
input, more complex input methods such as an input palettes may provide
entire words or phrases at once.

How does this differ from :py:meth:`~pyglet.window.Window.on_key_press`?

* Always use the :py:meth:`~pyglet.window.Window.on_text`
  event when you need a string from a series of keystrokes
* Never use the :py:meth:`~pyglet.window.Window.on_text` event when you
  need individual presses, such as controlling player movement in a game


.. _guide_keyboard-motion-events:

Motion events
^^^^^^^^^^^^^

In addition to key presses and entering new text, pyglet also supports common
text editing motions:

* Selecting text
* Moving the caret in response to non-character keys
* Deleting, copying, and pasting text

pyglet automatically detects and translates platform-specific versions of
supported motions into cross-platform
:py:meth:`~pyglet.window.Window.on_text_motion` events. These events are
intended be handled by the :py:meth:`Caret <pyglet.text.caret.Caret.on_text_motion>`
of any active :py:class:`~pyglet.text.layout.IncrementalTextLayout`, such
as those used in :py:class:`~pyglet.gui.widgets.TextEntry` fields.

The `motion` argument to the event handler will be a constant value
defined in :py:mod:`pyglet.window.key`. The table below lists the
supported text motions with their keyboard mapping on each supported
platform.

    .. list-table::
        :header-rows: 1

        * - Constant
          - Behaviour
          - Windows/Linux
          - Mac OS X
        * - ``MOTION_UP``
          - Move the cursor up
          - Up
          - Up
        * - ``MOTION_DOWN``
          - Move the cursor down
          - Down
          - Down
        * - ``MOTION_LEFT``
          - Move the cursor left
          - Left
          - Left
        * - ``MOTION_RIGHT``
          - Move the cursor right
          - Right
          - Right
        * - ``MOTION_COPY``
          - Copy the current selection to the clipboard
          - Ctrl + C
          - Command + C
        * - ``MOTION_PASTE``
          - Paste the clipboard contents into the current document
          - Ctrl + V
          - Command + V
        * - ``MOTION_PREVIOUS_WORD``
          - Move the cursor to the previous word
          - Ctrl + Left
          - Option + Left
        * - ``MOTION_NEXT_WORD``
          - Move the cursor to the next word
          - Ctrl + Right
          - Option + Right
        * - ``MOTION_BEGINNING_OF_LINE``
          - Move the cursor to the beginning of the current line
          - Home
          - Command + Left
        * - ``MOTION_END_OF_LINE``
          - Move the cursor to the end of the current line
          - End
          - Command + Right
        * - ``MOTION_PREVIOUS_PAGE``
          - Move to the previous page
          - Page Up
          - Page Up
        * - ``MOTION_NEXT_PAGE``
          - Move to the next page
          - Page Down
          - Page Down
        * - ``MOTION_BEGINNING_OF_FILE``
          - Move to the beginning of the document
          - Ctrl + Home
          - Home
        * - ``MOTION_END_OF_FILE``
          - Move to the end of the document
          - Ctrl + End
          - End
        * - ``MOTION_BACKSPACE``
          - Delete the previous character
          - Backspace
          - Backspace
        * - ``MOTION_DELETE``
          - Delete the next character, or the current character
          - Delete
          - Delete

If you believe pyglet needs to add support for a motion which is
currently missing, please skip to
:ref:`guide_keyboard-adding-new-motion-events`.

Customizing this behavior for an individual project is currently
difficult due to the way carets and text entry fields are interconnected.
However, using :py:meth:`~pyglet.window.Window.on_key_press` to handle
motion events should still be avoided for the following reasons:

* Supported platforms can assign a key to different motions. For example
  the Home key moves the cursor to the start of a line on Windows, but
  to the beginning of a document on Mac OS.
* Users expect holding down a motion's keys to repeat it released. For
  example, holding Backspace deletes multiple characters. However, only
  one :py:meth:`~pyglet.window.Window.on_key_press` event occurs per
  keypress.


.. _guide_keyboard-adding-new-motion-events:

Adding New Motions
""""""""""""""""""

Before adding a new motion, please do the following:

#. Consult the previous section & each platform's documentation to be
   sure it is:

   #. A common text operation present on every platform
   #. Not already implemented by pyglet

#. Attempt to find the corresponding functionality in
   `Apple's NSTextView documentation
   <https://developer.apple.com/documentation/appkit/nstextview/>`_

#. Discuss the addition and any remaining questions with maintainers by either:

   * `Filing a GitHub Issue <https://github.com/pyglet/pyglet/issues>`_
   * `Discord or the mailing list <https://github.com/pyglet/pyglet#contact>`_

Then, once you're ready:

#. Add the motion constant to :py:mod:`pyglet.window.key`

#. Add an entry for the constant in the :ref:`guide_keyboard-motion-events`
   section

#. Implement shared handling behavior in :py:meth:`~pyglet.text.caret.Caret.on_text_motion`

#. Implement Mac support (usually the most confusing step)

   #. Open `pyglet/window/cocoa/pyglet_textview.py
      <https://github.com/pyglet/pyglet/blob/master/pyglet/window/cocoa/pyglet_textview.py>`_
   #. Implement a corresponding handler method on
      ``PygletTextView_Implementation`` (pyglet's subclass of ``NSTextView``)

#. Add the Windows keyboard shortcut

   #. Open `pyglet/window/win32/__init__.py
      <https://github.com/pyglet/pyglet/blob/master/pyglet/window/win32/__init__.py>`_
   #. Add the keyboard shortcut to the ``_motion_map`` dictionary

#. Add the Linux keyboard shortcut

   #. Open `pyglet/window/xlib/__init__.py
      <https://github.com/pyglet/pyglet/blob/master/pyglet/window/xlib/__init__.py>`_
   #. Add the keyboard shortcut to the ``_motion_map`` dictionary


Be sure to test your changes before making a PR if possible!

If you do not have access to a specific platform above, include this in your PR's
notes.

Keyboard exclusivity
--------------------

Some keystrokes or key combinations normally bypass applications and are
handled by the operating system.  Some examples are Alt+Tab (Command+Tab on
Mac OS X) to switch applications and the keys mapped to Expose on Mac OS X.

You can disable these hot keys and have them behave as ordinary keystrokes for
your application.  This can be useful if you are developing a kiosk
application which should not be closed, or a game in which it is possible for
a user to accidentally press one of these keys.

To enable this mode, call
:py:meth:`Window.set_exclusive_keyboard <pyglet.window.Window.set_exclusive_keyboard>`
on the window  it should apply to. On Mac OS X, the dock and menu bar
will slide out of view while exclusive keyboard is activated.

The following restrictions apply on Windows:

* Only Alt+Tab can be disabled
* Users will still be able to switch applications through:

  * Ctrl+Escape
  * Alt+Escape
  * the Windows key
  * Ctrl+Alt+Delete

The following restrictions apply on Mac OS X:

* The power key is not disabled.

Use of this function is not recommended for general release applications or
games as it violates user-interface conventions.
