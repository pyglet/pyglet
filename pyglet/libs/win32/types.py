import ctypes
import sys

from ctypes import *
from ctypes.wintypes import *

from . import com


_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t
del t
del _int_types


class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]


def POINTER_(obj):
    p = ctypes.POINTER(obj)

    # Convert None to a real NULL pointer to work around bugs
    # in how ctypes handles None on 64-bit platforms
    if not isinstance(p.from_param, classmethod):
        def from_param(cls, x):
            if x is None:
                return cls()
            else:
                return x

        p.from_param = classmethod(from_param)

    return p


c_void_p = POINTER_(c_void)
INT = c_int
LPVOID = c_void_p
HCURSOR = HANDLE
LRESULT = LPARAM
COLORREF = DWORD
PVOID = c_void_p
WCHAR = c_wchar
BCHAR = c_wchar
LPRECT = POINTER(RECT)
LPPOINT = POINTER(POINT)
LPMSG = POINTER(MSG)
UINT_PTR = HANDLE
LONG_PTR = HANDLE
HDROP = HANDLE
LPTSTR = LPWSTR
LPSTREAM = c_void_p
CLSID = com.GUID

# Fixed in python 3.12. Is c_byte on other versions.
# Ensure it's the same across all versions.
if sys.version_info < (3, 12):
    BYTE = c_ubyte

LF_FACESIZE = 32
CCHDEVICENAME = 32
CCHFORMNAME = 32

WNDPROC = WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)
TIMERPROC = WINFUNCTYPE(None, HWND, UINT, POINTER(UINT), DWORD)
TIMERAPCPROC = WINFUNCTYPE(None, PVOID, DWORD, DWORD)
MONITORENUMPROC = WINFUNCTYPE(BOOL, HMONITOR, HDC, LPRECT, LPARAM)

PROCESS_DPI_AWARENESS = UINT
PROCESS_DPI_UNAWARE = 0
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2

MONITOR_DPI_TYPE = UINT
MDT_EFFECTIVE_DPI = 0
MDT_ANGULAR_DPI = 1
MDT_RAW_DPI = 2
MDT_DEFAULT = 3

DPI_AWARENESS_CONTEXT = HANDLE
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = DPI_AWARENESS_CONTEXT(-4)

MONITOR_DEFAULTTONEAREST = 0
MONITOR_DEFAULTTONULL = 1
MONITOR_DEFAULTTOPRIMARY = 2

def MAKEINTRESOURCE(i):
    return cast(ctypes.c_void_p(i & 0xFFFF), c_wchar_p)


class WNDCLASS(Structure):
    _fields_ = [
        ('style', UINT),
        ('lpfnWndProc', WNDPROC),
        ('cbClsExtra', c_int),
        ('cbWndExtra', c_int),
        ('hInstance', HINSTANCE),
        ('hIcon', HICON),
        ('hCursor', HCURSOR),
        ('hbrBackground', HBRUSH),
        ('lpszMenuName', c_char_p),
        ('lpszClassName', c_wchar_p)
    ]


class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [
        ("nLength", DWORD),
        ("lpSecurityDescriptor", c_void_p),
        ("bInheritHandle", BOOL)
    ]
    __slots__ = [f[0] for f in _fields_]


class PIXELFORMATDESCRIPTOR(Structure):
    _fields_ = [
        ('nSize', WORD),
        ('nVersion', WORD),
        ('dwFlags', DWORD),
        ('iPixelType', BYTE),
        ('cColorBits', BYTE),
        ('cRedBits', BYTE),
        ('cRedShift', BYTE),
        ('cGreenBits', BYTE),
        ('cGreenShift', BYTE),
        ('cBlueBits', BYTE),
        ('cBlueShift', BYTE),
        ('cAlphaBits', BYTE),
        ('cAlphaShift', BYTE),
        ('cAccumBits', BYTE),
        ('cAccumRedBits', BYTE),
        ('cAccumGreenBits', BYTE),
        ('cAccumBlueBits', BYTE),
        ('cAccumAlphaBits', BYTE),
        ('cDepthBits', BYTE),
        ('cStencilBits', BYTE),
        ('cAuxBuffers', BYTE),
        ('iLayerType', BYTE),
        ('bReserved', BYTE),
        ('dwLayerMask', DWORD),
        ('dwVisibleMask', DWORD),
        ('dwDamageMask', DWORD)
    ]


class RGBQUAD(Structure):
    _fields_ = [
        ('rgbBlue', BYTE),
        ('rgbGreen', BYTE),
        ('rgbRed', BYTE),
        ('rgbReserved', BYTE),
    ]
    __slots__ = [f[0] for f in _fields_]


class CIEXYZ(Structure):
    _fields_ = [
        ('ciexyzX', DWORD),
        ('ciexyzY', DWORD),
        ('ciexyzZ', DWORD),
    ]
    __slots__ = [f[0] for f in _fields_]


class CIEXYZTRIPLE(Structure):
    _fields_ = [
        ('ciexyzRed', CIEXYZ),
        ('ciexyzBlue', CIEXYZ),
        ('ciexyzGreen', CIEXYZ),
    ]
    __slots__ = [f[0] for f in _fields_]


class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ('biSize', DWORD),
        ('biWidth', LONG),
        ('biHeight', LONG),
        ('biPlanes', WORD),
        ('biBitCount', WORD),
        ('biCompression', DWORD),
        ('biSizeImage', DWORD),
        ('biXPelsPerMeter', LONG),
        ('biYPelsPerMeter', LONG),
        ('biClrUsed', DWORD),
        ('biClrImportant', DWORD),
    ]


class BITMAPV5HEADER(Structure):
    _fields_ = [
        ('bV5Size', DWORD),
        ('bV5Width', LONG),
        ('bV5Height', LONG),
        ('bV5Planes', WORD),
        ('bV5BitCount', WORD),
        ('bV5Compression', DWORD),
        ('bV5SizeImage', DWORD),
        ('bV5XPelsPerMeter', LONG),
        ('bV5YPelsPerMeter', LONG),
        ('bV5ClrUsed', DWORD),
        ('bV5ClrImportant', DWORD),
        ('bV5RedMask', DWORD),
        ('bV5GreenMask', DWORD),
        ('bV5BlueMask', DWORD),
        ('bV5AlphaMask', DWORD),
        ('bV5CSType', DWORD),
        ('bV5Endpoints', CIEXYZTRIPLE),
        ('bV5GammaRed', DWORD),
        ('bV5GammaGreen', DWORD),
        ('bV5GammaBlue', DWORD),
        ('bV5Intent', DWORD),
        ('bV5ProfileData', DWORD),
        ('bV5ProfileSize', DWORD),
        ('bV5Reserved', DWORD),
    ]


class BITMAPINFO(Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', RGBQUAD * 1)
    ]
    __slots__ = [f[0] for f in _fields_]


class LOGFONT(Structure):
    _fields_ = [
        ('lfHeight', LONG),
        ('lfWidth', LONG),
        ('lfEscapement', LONG),
        ('lfOrientation', LONG),
        ('lfWeight', LONG),
        ('lfItalic', BYTE),
        ('lfUnderline', BYTE),
        ('lfStrikeOut', BYTE),
        ('lfCharSet', BYTE),
        ('lfOutPrecision', BYTE),
        ('lfClipPrecision', BYTE),
        ('lfQuality', BYTE),
        ('lfPitchAndFamily', BYTE),
        ('lfFaceName', (c_char * LF_FACESIZE))  # Use ASCII
    ]


class LOGFONTW(Structure):
    # https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-logfontw
    _fields_ = [
        ('lfHeight', LONG),
        ('lfWidth', LONG),
        ('lfEscapement', LONG),
        ('lfOrientation', LONG),
        ('lfWeight', LONG),
        ('lfItalic', BYTE),
        ('lfUnderline', BYTE),
        ('lfStrikeOut', BYTE),
        ('lfCharSet', BYTE),
        ('lfOutPrecision', BYTE),
        ('lfClipPrecision', BYTE),
        ('lfQuality', BYTE),
        ('lfPitchAndFamily', BYTE),
        ('lfFaceName', (WCHAR * LF_FACESIZE))
    ]


class TRACKMOUSEEVENT(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('dwFlags', DWORD),
        ('hwndTrack', HWND),
        ('dwHoverTime', DWORD)
    ]
    __slots__ = [f[0] for f in _fields_]


class MINMAXINFO(Structure):
    _fields_ = [
        ('ptReserved', POINT),
        ('ptMaxSize', POINT),
        ('ptMaxPosition', POINT),
        ('ptMinTrackSize', POINT),
        ('ptMaxTrackSize', POINT)
    ]
    __slots__ = [f[0] for f in _fields_]


class ABC(Structure):
    _fields_ = [
        ('abcA', c_int),
        ('abcB', c_uint),
        ('abcC', c_int)
    ]
    __slots__ = [f[0] for f in _fields_]


class TEXTMETRIC(Structure):
    _fields_ = [
        ('tmHeight', c_long),
        ('tmAscent', c_long),
        ('tmDescent', c_long),
        ('tmInternalLeading', c_long),
        ('tmExternalLeading', c_long),
        ('tmAveCharWidth', c_long),
        ('tmMaxCharWidth', c_long),
        ('tmWeight', c_long),
        ('tmOverhang', c_long),
        ('tmDigitizedAspectX', c_long),
        ('tmDigitizedAspectY', c_long),
        ('tmFirstChar', c_char),  # Use ASCII
        ('tmLastChar', c_char),
        ('tmDefaultChar', c_char),
        ('tmBreakChar', c_char),
        ('tmItalic', c_byte),
        ('tmUnderlined', c_byte),
        ('tmStruckOut', c_byte),
        ('tmPitchAndFamily', c_byte),
        ('tmCharSet', c_byte)
    ]
    __slots__ = [f[0] for f in _fields_]


class MONITORINFOEX(Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', DWORD),
        ('szDevice', WCHAR * CCHDEVICENAME)
    ]
    __slots__ = [f[0] for f in _fields_]


class _DUMMYSTRUCTNAME(Structure):
    _fields_ = [
        ('dmOrientation', c_short),
        ('dmPaperSize', c_short),
        ('dmPaperLength', c_short),
        ('dmPaperWidth', c_short),
        ('dmScale', c_short),
        ('dmCopies', c_short),
        ('dmDefaultSource', c_short),
        ('dmPrintQuality', c_short),
    ]


class _DUMMYSTRUCTNAME2(Structure):
    _fields_ = [
        ('dmPosition', POINTL),
        ('dmDisplayOrientation', DWORD),
        ('dmDisplayFixedOutput', DWORD)
    ]


class _DUMMYDEVUNION(Union):
    _anonymous_ = ('_dummystruct1', '_dummystruct2')
    _fields_ = [
        ('_dummystruct1', _DUMMYSTRUCTNAME),
        ('dmPosition', POINTL),
        ('_dummystruct2', _DUMMYSTRUCTNAME2),
    ]


class DEVMODE(Structure):
    _anonymous_ = ('_dummyUnion',)
    _fields_ = [
        ('dmDeviceName', BCHAR * CCHDEVICENAME),
        ('dmSpecVersion', WORD),
        ('dmDriverVersion', WORD),
        ('dmSize', WORD),
        ('dmDriverExtra', WORD),
        ('dmFields', DWORD),
        # Just using the largest union member here
        ('_dummyUnion', _DUMMYDEVUNION),
        # End union
        ('dmColor', c_short),
        ('dmDuplex', c_short),
        ('dmYResolution', c_short),
        ('dmTTOption', c_short),
        ('dmCollate', c_short),
        ('dmFormName', BCHAR * CCHFORMNAME),
        ('dmLogPixels', WORD),
        ('dmBitsPerPel', DWORD),
        ('dmPelsWidth', DWORD),
        ('dmPelsHeight', DWORD),
        ('dmDisplayFlags', DWORD),  # union with dmNup
        ('dmDisplayFrequency', DWORD),
        ('dmICMMethod', DWORD),
        ('dmICMIntent', DWORD),
        ('dmDitherType', DWORD),
        ('dmReserved1', DWORD),
        ('dmReserved2', DWORD),
        ('dmPanningWidth', DWORD),
        ('dmPanningHeight', DWORD),
    ]


class ICONINFO(Structure):
    _fields_ = [
        ('fIcon', BOOL),
        ('xHotspot', DWORD),
        ('yHotspot', DWORD),
        ('hbmMask', HBITMAP),
        ('hbmColor', HBITMAP)
    ]
    __slots__ = [f[0] for f in _fields_]


class RAWINPUTDEVICE(Structure):
    _fields_ = [
        ('usUsagePage', USHORT),
        ('usUsage', USHORT),
        ('dwFlags', DWORD),
        ('hwndTarget', HWND)
    ]


PCRAWINPUTDEVICE = POINTER(RAWINPUTDEVICE)
HRAWINPUT = HANDLE


class RAWINPUTHEADER(Structure):
    _fields_ = [
        ('dwType', DWORD),
        ('dwSize', DWORD),
        ('hDevice', HANDLE),
        ('wParam', WPARAM),
    ]


class _Buttons(Structure):
    _fields_ = [
        ('usButtonFlags', USHORT),
        ('usButtonData', USHORT),
    ]


class _U(Union):
    _anonymous_ = ('_buttons',)
    _fields_ = [
        ('ulButtons', ULONG),
        ('_buttons', _Buttons),
    ]


class RAWMOUSE(Structure):
    _anonymous_ = ('u',)
    _fields_ = [
        ('usFlags', USHORT),
        ('u', _U),
        ('ulRawButtons', ULONG),
        ('lLastX', LONG),
        ('lLastY', LONG),
        ('ulExtraInformation', ULONG),
    ]


class RAWKEYBOARD(Structure):
    _fields_ = [
        ('MakeCode', USHORT),
        ('Flags', USHORT),
        ('Reserved', USHORT),
        ('VKey', USHORT),
        ('Message', UINT),
        ('ExtraInformation', ULONG),
    ]


class RAWHID(Structure):
    _fields_ = [
        ('dwSizeHid', DWORD),
        ('dwCount', DWORD),
        ('bRawData', POINTER(BYTE)),
    ]


class _RAWINPUTDEVICEUNION(Union):
    _fields_ = [
        ('mouse', RAWMOUSE),
        ('keyboard', RAWKEYBOARD),
        ('hid', RAWHID),
    ]


class RAWINPUT(Structure):
    _fields_ = [
        ('header', RAWINPUTHEADER),
        ('data', _RAWINPUTDEVICEUNION),
    ]


# PROPVARIANT wrapper, doesn't require InitPropVariantFromInt64 this way.
class _VarTable(Union):
    """Must be in an anonymous union or values will not work across various VT's."""
    _fields_ = [
        ('llVal', ctypes.c_longlong),
        ('pwszVal', LPWSTR)
    ]


class PROPVARIANT(Structure):
    _anonymous_ = ['union']

    _fields_ = [
        ('vt', ctypes.c_ushort),
        ('wReserved1', ctypes.c_ubyte),
        ('wReserved2', ctypes.c_ubyte),
        ('wReserved3', ctypes.c_ulong),
        ('union', _VarTable)
    ]


class _VarTableVariant(Union):
    """Must be in an anonymous union or values will not work across various VT's."""
    _fields_ = [
        ('bstrVal', LPCWSTR)
    ]


class VARIANT(Structure):
    _anonymous_ = ['union']

    _fields_ = [
        ('vt', ctypes.c_ushort),
        ('wReserved1', WORD),
        ('wReserved2', WORD),
        ('wReserved3', WORD),
        ('union', _VarTableVariant)
    ]


class DWM_BLURBEHIND(Structure):
    _fields_ = [
        ("dwFlags", DWORD),
        ("fEnable", BOOL),
        ("hRgnBlur", HRGN),
        ("fTransitionOnMaximized", DWORD),
    ]


class STATSTG(Structure):
    _fields_ = [
        ('pwcsName', LPOLESTR),
        ('type', DWORD),
        ('cbSize', ULARGE_INTEGER),
        ('mtime', FILETIME),
        ('ctime', FILETIME),
        ('atime', FILETIME),
        ('grfMode', DWORD),
        ('grfLocksSupported', DWORD),
        ('clsid', CLSID),
        ('grfStateBits', DWORD),
        ('reserved', DWORD),
    ]


class TIMECAPS(Structure):
    _fields_ = (('wPeriodMin', UINT),
                ('wPeriodMax', UINT))


class IStream(com.pIUnknown):
    _methods_ = [
        ('Read',
         com.STDMETHOD(c_void_p, ULONG, POINTER(ULONG))),
        ('Write',
         com.STDMETHOD()),
        ('Seek',
         com.STDMETHOD(LARGE_INTEGER, DWORD, POINTER(ULARGE_INTEGER))),
        ('SetSize',
         com.STDMETHOD()),
        ('CopyTo',
         com.STDMETHOD()),
        ('Commit',
         com.STDMETHOD()),
        ('Revert',
         com.STDMETHOD()),
        ('LockRegion',
         com.STDMETHOD()),
        ('UnlockRegion',
         com.STDMETHOD()),
        ('Stat',
         com.STDMETHOD(POINTER(STATSTG), UINT)),
        ('Clone',
         com.STDMETHOD()),
    ]


class DEV_BROADCAST_HDR(Structure):
    _fields_ = (
        ('dbch_size', DWORD),
        ('dbch_devicetype', DWORD),
        ('dbch_reserved', DWORD),
    )


class DEV_BROADCAST_DEVICEINTERFACE(Structure):
    _fields_ = (
        ('dbcc_size', DWORD),
        ('dbcc_devicetype', DWORD),
        ('dbcc_reserved', DWORD),
        ('dbcc_classguid', com.GUID),
        ('dbcc_name', ctypes.c_wchar * 256)
    )
