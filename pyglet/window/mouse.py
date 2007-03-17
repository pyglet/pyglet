#!/usr/bin/env python

'''Mouse constants and utilities for pyglet.window.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

def buttons_string(buttons):
    '''Return a string describing a set of active mouse buttons.

    Example::

        >>> buttons_string(MOUSE_LEFT_BUTTON | MOUSE_RIGHT_BUTTON)
        'MOUSE_LEFT_BUTTON|MOUSE_RIGHT_BUTTON'

    :Parameters:
        `buttons` : int
            Bitwise combination of mouse button constants.

    :rtype: str
    '''
    button_names = []
    if buttons & MOUSE_LEFT_BUTTON:
        button_names.append('MOUSE_LEFT_BUTTON')
    if buttons & MOUSE_MIDDLE_BUTTON:
        button_names.append('MOUSE_MIDDLE_BUTTON')
    if buttons & MOUSE_RIGHT_BUTTON:
        button_names.append('MOUSE_RIGHT_BUTTON')
    return '|'.join(button_names)

# Symbolic names for the mouse buttons
MOUSE_LEFT_BUTTON =   1 << 0
MOUSE_MIDDLE_BUTTON = 1 << 1
MOUSE_RIGHT_BUTTON =  1 << 2
