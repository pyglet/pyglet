.. _guide_working-with-the-keyboard:

Working with the keyboard
=========================

pyglet has support for low-level keyboard input suitable for games as well as
locale- and device-independent Unicode text entry.

Keyboard input requires a window which has focus.  The operating system
usually decides which application window has keyboard focus.  Typically this
window appears above all others and may be decorated differently, though this
is platform-specific (for example, Unix window managers sometimes couple
keyboard focus with the mouse pointer).

You can request keyboard focus for a window with the :py:meth:`~pyglet.window.Window.activate`
method, but you should not rely on this -- it may simply provide a visual cue to the user
indicating that the window requires user input, without actually getting
focus.

Windows created with the
:py:attr:`~pyglet.window.Window.WINDOW_STYLE_BORDERLESS` or
:py:attr:`~pyglet.window.Window.WINDOW_STYLE_TOOL`
style cannot receive keyboard focus.

It is not possible to use pyglet's keyboard or text events without a window;
consider using Python built-in functions such as ``input`` instead.

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
for many types of keyboard.  These are defined in :py:mod:`pyglet.window.key` as
constants.  For example, the Latin-1 alphabet is simply the letter itself::
    
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
(however they cannot all be distinguished on all platforms, including Mac OS
X)::

    key.LCTRL
    key.RCTRL
    key.LSHIFT
    key.RSHIFT
    ...

Key symbols are independent of any modifiers being held down.  For example,
lower-case and upper-case letters both generate the `A` symbol.  This is also
true of the number keypad.

Modifiers
^^^^^^^^^

The modifiers that are held down when the event is generated are combined in a
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
their Unicode representation will still be valid, see 
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

pyglet provides the convenience class :py:class:`~pyglet.window.key.KeyStateHandler` for storing the
current keyboard state.  This can be pushed onto the event handler stack of
any window and subsequently queried as a dict::

    from pyglet.window import key

    window = pyglet.window.Window()
    keys = key.KeyStateHandler()
    window.push_handlers(keys)

    # Check if the spacebar is currently pressed:
    if keys[key.SPACE]:
        pass

.. _guide_text-and-motion-events:

Text and motion events
----------------------

pyglet decouples the keys that the user presses from the Unicode text that is
input.  There are several benefits to this:

* The complex task of mapping modifiers and key symbols to Unicode characters
  is taken care of automatically and correctly.
* Key repeat is applied to keys held down according to the user's operating
  system preferences.
* Dead keys and compose keys are automatically interpreted to produce
  diacritic marks or combining characters.
* Keyboard input can be routed via an input palette, for example to input
  characters from Asian languages.
* Text input can come from other user-defined sources, such as handwriting or
  voice recognition.

The actual source of input (i.e., which keys were pressed, or what input
method was used) should be considered outside of the scope of the application
-- the operating system provides the necessary services.

When text is entered into a window, the :py:meth:`~pyglet.window.Window.on_text` event is fired::

    def on_text(text):
        pass

The only parameter provided is a Unicode string.  For keyboard input this will
usually be one character long, however more complex input methods such as an
input palette may provide an entire word or phrase at once.

You should always use the :py:meth:`~pyglet.window.Window.on_text` event when you need to determine a string
from a sequence of keystrokes.  Conversely, you never use :py:meth:`~pyglet.window.Window.on_text` when you
require keys to be pressed (for example, to control the movement of the player
in a game).

Motion events
^^^^^^^^^^^^^

In addition to entering text, users press keys on the keyboard to navigate
around text widgets according to well-ingrained conventions.  For example,
pressing the left arrow key moves the cursor one character to the left.

While you might be tempted to use the :py:meth:`~pyglet.window.Window.on_key_press` event to capture these
events, there are a couple of problems:

* Key repeat events are not generated for :py:meth:`~pyglet.window.Window.on_key_press`, yet users expect
  that holding down the left arrow key will eventually move the character to
  the beginning of the line.
* Different operating systems have different conventions for the behaviour of
  keys.  For example, on Windows it is customary for the Home key to move the
  cursor to the beginning of the line, whereas on Mac OS X the same key moves
  to the beginning of the document.

pyglet windows provide the :py:meth:`~pyglet.window.Window.on_text_motion` event, which takes care of these
problems by abstracting away the key presses and providing your application
only with the intended cursor motion::

    def on_text_motion(motion):
        pass

`motion` is an integer which is a constant defined in :py:mod:`pyglet.window.key`.
The following table shows the defined text motions and their keyboard mapping
on each operating system.

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
        * - ``MOTION_PREVIOUS_WORD``
          - Move the cursor to the previuos word
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

Keyboard exclusivity
--------------------

Some keystrokes or key combinations normally bypass applications and are
handled by the operating system.  Some examples are Alt+Tab (Command+Tab on
Mac OS X) to switch applications and the keys mapped to Expose on Mac OS X.

You can disable these hot keys and have them behave as ordinary keystrokes for
your application.  This can be useful if you are developing a kiosk
application which should not be closed, or a game in which it is possible for
a user to accidentally press one of these keys.

To enable this mode, call :py:meth:`~pyglet.window.Window.set_exclusive_keyboard` for the window on which it
should apply.  On Mac OS X the dock and menu bar will slide out of view while
exclusive keyboard is activated.

The following restrictions apply on Windows:

* Most keys are not disabled: a user can still switch away from your
  application using Ctrl+Escape, Alt+Escape, the Windows key or
  Ctrl+Alt+Delete.  Only the Alt+Tab combination is disabled.

The following restrictions apply on Mac OS X:

* The power key is not disabled.

Use of this function is not recommended for general release applications or
games as it violates user-interface conventions.
