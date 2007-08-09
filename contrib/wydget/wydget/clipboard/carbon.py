'''Clipboard implementation for OS X using Carbon

Based on information from:
  http://developer.apple.com/carbon/pasteboards.html
'''

import sys
from ctypes import *

import pyglet.lib
from pyglet.window.carbon import _create_cfstring, carbon, _oscheck
from pyglet.window.carbon.constants import *
from pyglet.window.carbon.types import *

carbon = pyglet.lib.load_library(
    framework='/System/Library/Frameworks/Carbon.framework')

PasteboardRef = c_void_p
PasteboardItemID = c_void_p
CFArrayRef = c_void_p
CFDataRef = c_void_p
ItemCount = c_int32
kPasteboardClipboard = _create_cfstring("com.apple.pasteboard.clipboard")
kPasteboardModified = 1 << 0
kPasteboardClientIsOwner = 1 << 1
utf16_plain_text = _create_cfstring("public.utf16-plain-text")
traditional_mac_plain_text = _create_cfstring("com.apple.traditional-mac-plain-text")

carbon.CFDataGetBytePtr.restype = POINTER(c_char)


class CarbonPasteboard(object):
    def __init__(self):
        self.pasteboard = PasteboardRef()
        carbon.PasteboardCreate(kPasteboardClipboard, byref(self.pasteboard))

    def get_text(self):
        # get pasteboard item count
        item_count = ItemCount()
        _oscheck(carbon.PasteboardGetItemCount(self.pasteboard,
            byref(item_count)))

        item_id = PasteboardItemID()
        flavor_type_array = CFArrayRef()
        flavor_data = CFDataRef()
        for item_index in range(1, item_count.value + 1):
            # get pasteboard item
            _oscheck(carbon.PasteboardGetItemIdentifier(self.pasteboard,
                item_index, byref(item_id)))
      
            # get pasteboard item flavor type array
            _oscheck(carbon.PasteboardCopyItemFlavors(self.pasteboard, item_id, 
                byref(flavor_type_array)))
            flavor_count = carbon.CFArrayGetCount(flavor_type_array)

            try:
                # Look for UTF-16 value first
                for flavor_index in range(flavor_count):
                    flavor_type = carbon.CFArrayGetValueAtIndex(
                        flavor_type_array, flavor_index)
                    if carbon.UTTypeConformsTo(flavor_type, utf16_plain_text):
                        # get flavor data
                        _oscheck(carbon.PasteboardCopyItemFlavorData(
                            self.pasteboard, item_id, flavor_type,
                            byref(flavor_data)))
                        try:
                            data = carbon.CFDataGetBytePtr(flavor_data)
                            length = carbon.CFDataGetLength(flavor_data)
                            s = str(data[:length])
                            if sys.byteorder == 'big':
                                return s.decode('utf_16_be')
                            else:
                                return s.decode('utf_16_le')   # explicit endian avoids BOM
                        finally:
                            carbon.CFRelease (flavor_data)

                # Look for TEXT value if no UTF-16 value
                for flavor_index in range(flavor_count):
                    flavor_type = carbon.CFArrayGetValueAtIndex(
                        flavor_type_array, flavor_index)
                    if carbon.UTTypeConformsTo(flavor_type,
                            traditional_mac_plain_text):
                        # get flavor data
                        _oscheck(carbon.PasteboardCopyItemFlavorData(
                            self.pasteboard, item_id, flavor_type,
                            byref(flavor_data)))
                        try:
                            data = carbon.CFDataGetBytePtr(flavor_data)
                            length = carbon.CFDataGetLength(flavor_data)
                            return str(data[:length])
                        finally:
                            carbon.CFRelease (flavor_data)
            finally:
                carbon.CFRelease(flavor_type_array)

        return None
      
    def put_text(self, text):
        if not text: return

        # clear pasteboard
        _oscheck(carbon.PasteboardClear(self.pasteboard))
  
        sync_flags = carbon.PasteboardSynchronize(self.pasteboard)
  
        if sync_flags & kPasteboardModified:
            raise ValueError, "Pasteboard not synchronized after clear"
  
        if not sync_flags & kPasteboardClientIsOwner:
            raise ValueError, "Pasteboard not owned after clear"

        if sys.byteorder == 'big':
            utf16_data = text.encode('utf_16_be')
        else:
            utf16_data = text.encode('utf_16_le')   # explicit endian avoids BOM
        data_ref = carbon.CFDataCreate(None, utf16_data, len(utf16_data))
        if not data_ref:
            raise ValueError, "Can't create unicode data for pasteboard"
  
        # put unicode to pasteboard
        try:
            _oscheck(carbon.PasteboardPutItemFlavor(self.pasteboard,
                1, utf16_plain_text, data_ref, 0))
        finally:
            carbon.CFRelease(data_ref)
  
        ascii_data = text.encode('ascii', 'replace')
        data_ref = carbon.CFDataCreate(None, ascii_data, len(ascii_data))
        if not data_ref:
            raise ValueError, "Can't create text data for pasteboard"

        # put text to pasteboard
        try:
            _oscheck(carbon.PasteboardPutItemFlavor(self.pasteboard,
                1, traditional_mac_plain_text, data_ref, 0))
        finally:
            carbon.CFRelease(data_ref)

if __name__ == '__main__':
    clipboard = CarbonPasteboard()
    print `clipboard.get_text()`

    if len(sys.argv) > 1:
        clipboard.put_text(''.join(sys.argv[1:]).decode('utf8'))

