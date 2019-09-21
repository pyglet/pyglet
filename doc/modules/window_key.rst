pyglet.window.key
===============================================================

.. automodule:: pyglet.window.key
  :members: KeyStateHandler, modifiers_string, symbol_string, motion_string, 
            user_key

Key Constants
-------------

Modifier mask constants
^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::

  *
    * ``MOD_SHIFT``
  *
    * ``MOD_CTRL``
  *
    * ``MOD_ALT``
  *
    * ``MOD_CAPSLOCK``
  *
    * ``MOD_NUMLOCK``
  *
    * ``MOD_WINDOWS``
  *
    * ``MOD_COMMAND``
  *
    * ``MOD_OPTION``
  *
    * ``MOD_SCROLLLOCK``
  *
    * ``MOD_FUNCTION``
  *
    * ``MOD_ACCEL`` (``MOD_CTRL`` on Windows & Linux, ``MOD_CMD`` on OS X)

ASCII commands
^^^^^^^^^^^^^^

.. list-table::

  *
    * ``BACKSPACE``
  *
    * ``TAB``
  *
    * ``LINEFEED``
  *
    * ``CLEAR``
  *
    * ``RETURN``
  *
    * ``ENTER``
  *
    * ``PAUSE``
  *
    * ``SCROLLLOCK``
  *
    * ``SYSREQ``
  *
    * ``ESCAPE``
  *
    * ``SPACE``

Cursor control and motion
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::

  *
    * ``HOME``
  *
    * ``LEFT``
  *
    * ``UP``
  *
    * ``RIGHT``
  *
    * ``DOWN``
  *
    * ``PAGEUP``
  *
    * ``PAGEDOWN``
  *
    * ``END``
  *
    * ``BEGIN``

Misc functions
^^^^^^^^^^^^^^

.. list-table::

  *
    * ``DELETE``
  *
    * ``SELECT``
  *
    * ``PRINT``
  *
    * ``EXECUTE``
  *
    * ``INSERT``
  *
    * ``UNDO``
  *
    * ``REDO``
  *
    * ``MENU``
  *
    * ``FIND``
  *
    * ``CANCEL``
  *
    * ``HELP``
  *
    * ``BREAK``
  *
    * ``MODESWITCH``
  *
    * ``SCRIPTSWITCH``
  *
    * ``FUNCTION``

Text motion constants
^^^^^^^^^^^^^^^^^^^^^

These are allowed to clash with key constants.

.. list-table::

  *
    * ``MOTION_UP``
  *
    * ``MOTION_RIGHT``
  *
    * ``MOTION_DOWN``
  *
    * ``MOTION_LEFT``
  *
    * ``MOTION_NEXT_WORD``
  *
    * ``MOTION_PREVIOUS_WORD``
  *
    * ``MOTION_BEGINNING_OF_LINE``
  *
    * ``MOTION_END_OF_LINE``
  *
    * ``MOTION_NEXT_PAGE``
  *
    * ``MOTION_PREVIOUS_PAGE``
  *
    * ``MOTION_BEGINNING_OF_FILE``
  *
    * ``MOTION_END_OF_FILE``
  *
    * ``MOTION_BACKSPACE``
  *
    * ``MOTION_DELETE``

Number pad
^^^^^^^^^^

.. list-table::

  *
    * ``NUMLOCK``
  *
    * ``NUM_SPACE``
  *
    * ``NUM_TAB``
  *
    * ``NUM_ENTER``
  *
    * ``NUM_F1``
  *
    * ``NUM_F2``
  *
    * ``NUM_F3``
  *
    * ``NUM_F4``
  *
    * ``NUM_HOME``
  *
    * ``NUM_LEFT``
  *
    * ``NUM_UP``
  *
    * ``NUM_RIGHT``
  *
    * ``NUM_DOWN``
  *
    * ``NUM_PRIOR``
  *
    * ``NUM_PAGE_UP``
  *
    * ``NUM_NEXT``
  *
    * ``NUM_PAGE_DOWN``
  *
    * ``NUM_END``
  *
    * ``NUM_BEGIN``
  *
    * ``NUM_INSERT``
  *
    * ``NUM_DELETE``
  *
    * ``NUM_EQUAL``
  *
    * ``NUM_MULTIPLY``
  *
    * ``NUM_ADD``
  *
    * ``NUM_SEPARATOR``
  *
    * ``NUM_SUBTRACT``
  *
    * ``NUM_DECIMAL``
  *
    * ``NUM_DIVIDE``
  *
    * ``NUM_0``
  *
    * ``NUM_1``
  *
    * ``NUM_2``
  *
    * ``NUM_3``
  *
    * ``NUM_4``
  *
    * ``NUM_5``
  *
    * ``NUM_6``
  *
    * ``NUM_7``
  *
    * ``NUM_8``
  *
    * ``NUM_9``

Function keys
^^^^^^^^^^^^^

.. list-table::

  *
    * ``F1``
  *
    * ``F2``
  *
    * ``F3``
  *
    * ``F4``
  *
    * ``F5``
  *
    * ``F6``
  *
    * ``F7``
  *
    * ``F8``
  *
    * ``F9``
  *
    * ``F10``
  *
    * ``F11``
  *
    * ``F12``
  *
    * ``F13``
  *
    * ``F14``
  *
    * ``F15``
  *
    * ``F16``
  *
    * ``F17``
  *
    * ``F18``
  *
    * ``F19``
  *
    * ``F20``

Modifiers
^^^^^^^^^

.. list-table::

  *
    * ``LSHIFT``
  *
    * ``RSHIFT``
  *
    * ``LCTRL``
  *
    * ``RCTRL``
  *
    * ``CAPSLOCK``
  *
    * ``LMETA``
  *
    * ``RMETA``
  *
    * ``LALT``
  *
    * ``RALT``
  *
    * ``LWINDOWS``
  *
    * ``RWINDOWS``
  *
    * ``LCOMMAND``
  *
    * ``RCOMMAND``
  *
    * ``LOPTION``
  *
    * ``ROPTION``

Latin-1
^^^^^^^

.. list-table::

  *
    * ``SPACE``
  *
    * ``EXCLAMATION``
  *
    * ``DOUBLEQUOTE``
  *
    * ``HASH``
  *
    * ``POUND``
  *
    * ``DOLLAR``
  *
    * ``PERCENT``
  *
    * ``AMPERSAND``
  *
    * ``APOSTROPHE``
  *
    * ``PARENLEFT``
  *
    * ``PARENRIGHT``
  *
    * ``ASTERISK``
  *
    * ``PLUS``
  *
    * ``COMMA``
  *
    * ``MINUS``
  *
    * ``PERIOD``
  *
    * ``SLASH``
  *
    * ``_0``
  *
    * ``_1``
  *
    * ``_2``
  *
    * ``_3``
  *
    * ``_4``
  *
    * ``_5``
  *
    * ``_6``
  *
    * ``_7``
  *
    * ``_8``
  *
    * ``_9``
  *
    * ``COLON``
  *
    * ``SEMICOLON``
  *
    * ``LESS``
  *
    * ``EQUAL``
  *
    * ``GREATER``
  *
    * ``QUESTION``
  *
    * ``AT``
  *
    * ``BRACKETLEFT``
  *
    * ``BACKSLASH``
  *
    * ``BRACKETRIGHT``
  *
    * ``ASCIICIRCUM``
  *
    * ``UNDERSCORE``
  *
    * ``GRAVE``
  *
    * ``QUOTELEFT``
  *
    * ``A``
  *
    * ``B``
  *
    * ``C``
  *
    * ``D``
  *
    * ``E``
  *
    * ``F``
  *
    * ``G``
  *
    * ``H``
  *
    * ``I``
  *
    * ``J``
  *
    * ``K``
  *
    * ``L``
  *
    * ``M``
  *
    * ``N``
  *
    * ``O``
  *
    * ``P``
  *
    * ``Q``
  *
    * ``R``
  *
    * ``S``
  *
    * ``T``
  *
    * ``U``
  *
    * ``V``
  *
    * ``W``
  *
    * ``X``
  *
    * ``Y``
  *
    * ``Z``
  *
    * ``BRACELEFT``
  *
    * ``BAR``
  *
    * ``BRACERIGHT``
  *
    * ``ASCIITILDE``