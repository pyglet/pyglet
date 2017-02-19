'''Clipboard implementation for OS X using Win32

Based on implementation from:

http://aspn.activestate.com/ASPN/Mail/Message/ctypes-users/1771866
'''
from ctypes import *
from pyglet.window.win32.constants import CF_TEXT, GHND

OpenClipboard = windll.user32.OpenClipboard
EmptyClipboard = windll.user32.EmptyClipboard
GetClipboardData = windll.user32.GetClipboardData
SetClipboardData = windll.user32.SetClipboardData
IsClipboardFormatAvailable = windll.user32.IsClipboardFormatAvailable
CloseClipboard = windll.user32.CloseClipboard
GlobalLock = windll.kernel32.GlobalLock
GlobalAlloc = windll.kernel32.GlobalAlloc
GlobalUnlock = windll.kernel32.GlobalUnlock
memcpy = cdll.msvcrt.memcpy


class Win32Clipboard(object):

    def get_text(self):
        # XXX Doesn't handle CF_UNICODETEXT yet.
        if not IsClipboardFormatAvailable(CF_TEXT):
            return ''
        if not OpenClipboard(c_int(0)):
            return ''
        try:
            hClipMem = GetClipboardData(c_int(CF_TEXT))
            GlobalLock.restype = c_char_p
            text = GlobalLock(c_int(hClipMem))
            GlobalUnlock(c_int(hClipMem))
        finally:
            CloseClipboard()
        return text.decode('windows-1252')

    def put_text(self, text):
        # XXX Doesn't handle CF_UNICODETEXT yet.
        buffer = c_buffer(text)
        bufferSize = sizeof(buffer)
        hGlobalMem = GlobalAlloc(c_int(GHND), c_int(bufferSize))
        GlobalLock.restype = c_void_p
        lpGlobalMem = GlobalLock(c_int(hGlobalMem))
        memcpy(lpGlobalMem, addressof(buffer), c_int(bufferSize))
        GlobalUnlock(c_int(hGlobalMem))
        if OpenClipboard(0):
            EmptyClipboard()
            SetClipboardData(c_int(CF_TEXT), c_int(hGlobalMem))
            CloseClipboard()

if __name__ == '__main__':
    cb = Win32Clipboard()
    print 'GOT', `cb.get_text()`             # display last text clipped
    cb.set_text("[Clipboard text replaced]") # replace it
    print 'GOT', `cb.get_text()`             # display new clipboard

