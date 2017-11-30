'''Interaction with the Operating System text clipboard
'''

import sys

def get_text():
    '''Get a string from the clipboard.
    '''
    return _clipboard.get_text()

def put_text(text):
    '''Put the string onto the clipboard.
    '''
    return _clipboard.put_text(text)

# Try to determine which platform to use.
if sys.platform == 'darwin':
    assert false
    _clipboard = None
elif sys.platform in ('win32', 'cygwin'):
    from wydget.clipboard.win32 import Win32Clipboard
    _clipboard = Win32Clipboard()
else:
    from wydget.clipboard.xlib import XlibClipboard
    _clipboard = XlibClipboard()

