# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2023 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import atexit
import struct
import warnings

import pyglet
from . import com
from . import constants
from .types import *

IS64 = struct.calcsize("P") == 8

_debug_win32 = pyglet.options['debug_win32']

DebugLibrary = lambda lib: ctypes.WinDLL(lib, use_last_error=True if _debug_win32 else False)

_gdi32 = DebugLibrary('gdi32')
_kernel32 = DebugLibrary('kernel32')
_user32 = DebugLibrary('user32')
_dwmapi = DebugLibrary('dwmapi')
_shell32 = DebugLibrary('shell32')
_ole32 = DebugLibrary('ole32')
_oleaut32 = DebugLibrary('oleaut32')

# _gdi32
_gdi32.AddFontMemResourceEx.restype = HANDLE
_gdi32.AddFontMemResourceEx.argtypes = [PVOID, DWORD, PVOID, POINTER(DWORD)]
_gdi32.ChoosePixelFormat.restype = c_int
_gdi32.ChoosePixelFormat.argtypes = [HDC, POINTER(PIXELFORMATDESCRIPTOR)]
_gdi32.CreateBitmap.restype = HBITMAP
_gdi32.CreateBitmap.argtypes = [c_int, c_int, UINT, UINT, c_void_p]
_gdi32.CreateCompatibleDC.restype = HDC
_gdi32.CreateCompatibleDC.argtypes = [HDC]
_gdi32.CreateDIBitmap.restype = HBITMAP
_gdi32.CreateDIBitmap.argtypes = [HDC, POINTER(BITMAPINFOHEADER), DWORD, c_void_p, POINTER(BITMAPINFO), UINT]
_gdi32.CreateDIBSection.restype = HBITMAP
_gdi32.CreateDIBSection.argtypes = [HDC, c_void_p, UINT, c_void_p, HANDLE, DWORD]  # POINTER(BITMAPINFO)
_gdi32.CreateFontIndirectA.restype = HFONT
_gdi32.CreateFontIndirectA.argtypes = [POINTER(LOGFONT)]
_gdi32.CreateFontIndirectW.restype = HFONT
_gdi32.CreateFontIndirectW.argtypes = [POINTER(LOGFONTW)]
_gdi32.DeleteDC.restype = BOOL
_gdi32.DeleteDC.argtypes = [HDC]
_gdi32.DeleteObject.restype = BOOL
_gdi32.DeleteObject.argtypes = [HGDIOBJ]
_gdi32.DescribePixelFormat.restype = c_int
_gdi32.DescribePixelFormat.argtypes = [HDC, c_int, UINT, POINTER(PIXELFORMATDESCRIPTOR)]
_gdi32.ExtTextOutA.restype = BOOL
_gdi32.ExtTextOutA.argtypes = [HDC, c_int, c_int, UINT, LPRECT, c_char_p, UINT, POINTER(INT)]
_gdi32.GdiFlush.restype = BOOL
_gdi32.GdiFlush.argtypes = []
_gdi32.GetCharABCWidthsW.restype = BOOL
_gdi32.GetCharABCWidthsW.argtypes = [HDC, UINT, UINT, POINTER(ABC)]
_gdi32.GetCharWidth32W.restype = BOOL
_gdi32.GetCharWidth32W.argtypes = [HDC, UINT, UINT, POINTER(INT)]
_gdi32.GetStockObject.restype = HGDIOBJ
_gdi32.GetStockObject.argtypes = [c_int]
_gdi32.GetTextMetricsA.restype = BOOL
_gdi32.GetTextMetricsA.argtypes = [HDC, POINTER(TEXTMETRIC)]
_gdi32.SelectObject.restype = HGDIOBJ
_gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
_gdi32.SetBkColor.restype = COLORREF
_gdi32.SetBkColor.argtypes = [HDC, COLORREF]
_gdi32.SetBkMode.restype = c_int
_gdi32.SetBkMode.argtypes = [HDC, c_int]
_gdi32.SetPixelFormat.restype = BOOL
_gdi32.SetPixelFormat.argtypes = [HDC, c_int, POINTER(PIXELFORMATDESCRIPTOR)]
_gdi32.SetTextColor.restype = COLORREF
_gdi32.SetTextColor.argtypes = [HDC, COLORREF]
_gdi32.SwapBuffers.restype = BOOL
_gdi32.SwapBuffers.argtypes = [HDC]

_kernel32.CloseHandle.restype = BOOL
_kernel32.CloseHandle.argtypes = [HANDLE]
_kernel32.CreateEventW.restype = HANDLE
_kernel32.CreateEventW.argtypes = [POINTER(SECURITY_ATTRIBUTES), BOOL, BOOL, c_wchar_p]
_kernel32.CreateWaitableTimerA.restype = HANDLE
_kernel32.CreateWaitableTimerA.argtypes = [POINTER(SECURITY_ATTRIBUTES), BOOL, c_char_p]
_kernel32.GetCurrentThreadId.restype = DWORD
_kernel32.GetCurrentThreadId.argtypes = []
_kernel32.GetModuleHandleW.restype = HMODULE
_kernel32.GetModuleHandleW.argtypes = [c_wchar_p]
_kernel32.GlobalAlloc.restype = HGLOBAL
_kernel32.GlobalAlloc.argtypes = [UINT, c_size_t]
_kernel32.GlobalLock.restype = LPVOID
_kernel32.GlobalLock.argtypes = [HGLOBAL]
_kernel32.GlobalUnlock.restype = BOOL
_kernel32.GlobalUnlock.argtypes = [HGLOBAL]
_kernel32.SetLastError.restype = DWORD
_kernel32.SetLastError.argtypes = [DWORD]
_kernel32.SetWaitableTimer.restype = BOOL
_kernel32.SetWaitableTimer.argtypes = [HANDLE, POINTER(LARGE_INTEGER), LONG, LPVOID, LPVOID, BOOL]  # TIMERAPCPROC
_kernel32.WaitForSingleObject.restype = DWORD
_kernel32.WaitForSingleObject.argtypes = [HANDLE, DWORD]

_user32.AdjustWindowRectEx.restype = BOOL
_user32.AdjustWindowRectEx.argtypes = [LPRECT, DWORD, BOOL, DWORD]
_user32.ChangeDisplaySettingsExW.restype = LONG
_user32.ChangeDisplaySettingsExW.argtypes = [c_wchar_p, POINTER(DEVMODE), HWND, DWORD, LPVOID]
_user32.ClientToScreen.restype = BOOL
_user32.ClientToScreen.argtypes = [HWND, LPPOINT]
_user32.ClipCursor.restype = BOOL
_user32.ClipCursor.argtypes = [LPRECT]
_user32.CreateIconIndirect.restype = HICON
_user32.CreateIconIndirect.argtypes = [POINTER(ICONINFO)]
_user32.CreateWindowExW.restype = HWND
_user32.CreateWindowExW.argtypes = [DWORD, c_wchar_p, c_wchar_p, DWORD, c_int, c_int, c_int, c_int, HWND, HMENU,
                                    HINSTANCE, LPVOID]
_user32.DefWindowProcW.restype = LRESULT
_user32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
_user32.DestroyWindow.restype = BOOL
_user32.DestroyWindow.argtypes = [HWND]
_user32.DispatchMessageW.restype = LRESULT
_user32.DispatchMessageW.argtypes = [LPMSG]
_user32.EnumDisplayMonitors.restype = BOOL
_user32.EnumDisplayMonitors.argtypes = [HDC, LPRECT, MONITORENUMPROC, LPARAM]
_user32.EnumDisplaySettingsW.restype = BOOL
_user32.EnumDisplaySettingsW.argtypes = [c_wchar_p, DWORD, POINTER(DEVMODE)]
_user32.FillRect.restype = c_int
_user32.FillRect.argtypes = [HDC, LPRECT, HBRUSH]
_user32.GetClientRect.restype = BOOL
_user32.GetClientRect.argtypes = [HWND, LPRECT]
_user32.GetCursorPos.restype = BOOL
_user32.GetCursorPos.argtypes = [LPPOINT]
# workaround for win 64-bit, see issue #664
_user32.GetDC.restype = c_void_p  # HDC
_user32.GetDC.argtypes = [c_void_p]  # [HWND]
_user32.GetDesktopWindow.restype = HWND
_user32.GetDesktopWindow.argtypes = []
_user32.GetKeyState.restype = c_short
_user32.GetKeyState.argtypes = [c_int]
_user32.GetMessageW.restype = BOOL
_user32.GetMessageW.argtypes = [LPMSG, HWND, UINT, UINT]
_user32.GetMonitorInfoW.restype = BOOL
_user32.GetMonitorInfoW.argtypes = [HMONITOR, POINTER(MONITORINFOEX)]
_user32.GetQueueStatus.restype = DWORD
_user32.GetQueueStatus.argtypes = [UINT]
_user32.GetSystemMetrics.restype = c_int
_user32.GetSystemMetrics.argtypes = [c_int]
_user32.LoadCursorW.restype = HCURSOR
_user32.LoadCursorW.argtypes = [HINSTANCE, c_wchar_p]
_user32.LoadIconW.restype = HICON
_user32.LoadIconW.argtypes = [HINSTANCE, c_wchar_p]
_user32.LoadImageW.restype = HICON
_user32.LoadImageW.argtypes = [HINSTANCE, LPCWSTR, UINT, c_int, c_int, UINT]
_user32.MapVirtualKeyW.restype = UINT
_user32.MapVirtualKeyW.argtypes = [UINT, UINT]
_user32.MapWindowPoints.restype = c_int
_user32.MapWindowPoints.argtypes = [HWND, HWND, c_void_p, UINT]  # HWND, HWND, LPPOINT, UINT
_user32.MsgWaitForMultipleObjects.restype = DWORD
_user32.MsgWaitForMultipleObjects.argtypes = [DWORD, POINTER(HANDLE), BOOL, DWORD, DWORD]
_user32.PeekMessageW.restype = BOOL
_user32.PeekMessageW.argtypes = [LPMSG, HWND, UINT, UINT, UINT]
_user32.PostThreadMessageW.restype = BOOL
_user32.PostThreadMessageW.argtypes = [DWORD, UINT, WPARAM, LPARAM]
_user32.RegisterClassW.restype = ATOM
_user32.RegisterClassW.argtypes = [POINTER(WNDCLASS)]
_user32.RegisterHotKey.restype = BOOL
_user32.RegisterHotKey.argtypes = [HWND, c_int, UINT, UINT]
_user32.ReleaseCapture.restype = BOOL
_user32.ReleaseCapture.argtypes = []
# workaround for win 64-bit, see issue #664
_user32.ReleaseDC.restype = c_int32  # c_int
_user32.ReleaseDC.argtypes = [c_void_p, c_void_p]  # [HWND, HDC]
_user32.ScreenToClient.restype = BOOL
_user32.ScreenToClient.argtypes = [HWND, LPPOINT]
_user32.SetCapture.restype = HWND
_user32.SetCapture.argtypes = [HWND]
_user32.SetClassLongW.restype = DWORD
_user32.SetClassLongW.argtypes = [HWND, c_int, LONG]
if IS64:
    _user32.SetClassLongPtrW.restype = ULONG
    _user32.SetClassLongPtrW.argtypes = [HWND, c_int, LONG_PTR]
else:
    _user32.SetClassLongPtrW = _user32.SetClassLongW
_user32.SetCursor.restype = HCURSOR
_user32.SetCursor.argtypes = [HCURSOR]
_user32.SetCursorPos.restype = BOOL
_user32.SetCursorPos.argtypes = [c_int, c_int]
_user32.SetFocus.restype = HWND
_user32.SetFocus.argtypes = [HWND]
_user32.SetForegroundWindow.restype = BOOL
_user32.SetForegroundWindow.argtypes = [HWND]
_user32.SetTimer.restype = UINT_PTR
_user32.SetTimer.argtypes = [HWND, UINT_PTR, UINT, TIMERPROC]
_user32.SetWindowLongW.restype = LONG
_user32.SetWindowLongW.argtypes = [HWND, c_int, LONG]
_user32.SetWindowPos.restype = BOOL
_user32.SetWindowPos.argtypes = [HWND, HWND, c_int, c_int, c_int, c_int, UINT]
_user32.SetWindowTextW.restype = BOOL
_user32.SetWindowTextW.argtypes = [HWND, c_wchar_p]
_user32.ShowCursor.restype = c_int
_user32.ShowCursor.argtypes = [BOOL]
_user32.ShowWindow.restype = BOOL
_user32.ShowWindow.argtypes = [HWND, c_int]
_user32.TrackMouseEvent.restype = BOOL
_user32.TrackMouseEvent.argtypes = [POINTER(TRACKMOUSEEVENT)]
_user32.TranslateMessage.restype = BOOL
_user32.TranslateMessage.argtypes = [LPMSG]
_user32.UnregisterClassW.restype = BOOL
_user32.UnregisterClassW.argtypes = [c_wchar_p, HINSTANCE]
_user32.UnregisterHotKey.restype = BOOL
_user32.UnregisterHotKey.argtypes = [HWND, c_int]
# Raw inputs
_user32.RegisterRawInputDevices.restype = BOOL
_user32.RegisterRawInputDevices.argtypes = [PCRAWINPUTDEVICE, UINT, UINT]
_user32.GetRawInputData.restype = UINT
_user32.GetRawInputData.argtypes = [HRAWINPUT, UINT, LPVOID, PUINT, UINT]
_user32.ChangeWindowMessageFilterEx.restype = BOOL
_user32.ChangeWindowMessageFilterEx.argtypes = [HWND, UINT, DWORD, c_void_p]

# dwmapi
_dwmapi.DwmIsCompositionEnabled.restype = c_int
_dwmapi.DwmIsCompositionEnabled.argtypes = [POINTER(INT)]
_dwmapi.DwmFlush.restype = c_int
_dwmapi.DwmFlush.argtypes = []

# _shell32
_shell32.DragAcceptFiles.restype = c_void
_shell32.DragAcceptFiles.argtypes = [HWND, BOOL]
_shell32.DragFinish.restype = c_void
_shell32.DragFinish.argtypes = [HDROP]
_shell32.DragQueryFileW.restype = UINT
_shell32.DragQueryFileW.argtypes = [HDROP, UINT, LPWSTR, UINT]
_shell32.DragQueryPoint.restype = BOOL
_shell32.DragQueryPoint.argtypes = [HDROP, LPPOINT]

# ole32
_ole32.CreateStreamOnHGlobal.argtypes = [HGLOBAL, BOOL, LPSTREAM]
_ole32.CoInitialize.restype = HRESULT
_ole32.CoInitialize.argtypes = [LPVOID]
_ole32.CoInitializeEx.restype = HRESULT
_ole32.CoInitializeEx.argtypes = [LPVOID, DWORD]
_ole32.CoUninitialize.restype = HRESULT
_ole32.CoUninitialize.argtypes = []
_ole32.PropVariantClear.restype = HRESULT
_ole32.PropVariantClear.argtypes = [c_void_p]
_ole32.CoCreateInstance.restype = HRESULT
_ole32.CoCreateInstance.argtypes = [com.REFIID, c_void_p, DWORD, com.REFIID, c_void_p]
_ole32.CoSetProxyBlanket.restype = HRESULT
_ole32.CoSetProxyBlanket.argtypes = (c_void_p, DWORD, DWORD, c_void_p, DWORD, DWORD, c_void_p, DWORD)

# oleaut32
_oleaut32.VariantInit.restype = c_void_p
_oleaut32.VariantInit.argtypes = [c_void_p]
_oleaut32.VariantClear.restype = HRESULT
_oleaut32.VariantClear.argtypes = [c_void_p]

if _debug_win32:
    import traceback

    _log_win32 = open('debug_win32.log', 'w')


    def win32_errcheck(result, func, args):
        last_err = ctypes.get_last_error()
        if last_err != 0:  # If the result is not success and last error is invalid.
            for entry in traceback.format_list(traceback.extract_stack()[:-1]):
                _log_win32.write(entry)
            print(f"[Result {result}] Error #{last_err} - {ctypes.FormatError(last_err)}", file=_log_win32)
        return args


    def set_errchecks(lib):
        """Set errcheck hook on all functions we have defined."""
        for key in lib.__dict__:
            if key.startswith('_'):  # Ignore builtins.
                continue
            lib.__dict__[key].errcheck = win32_errcheck


    set_errchecks(_gdi32)
    set_errchecks(_kernel32)
    set_errchecks(_user32)
    set_errchecks(_dwmapi)
    set_errchecks(_shell32)
    set_errchecks(_ole32)
    set_errchecks(_oleaut32)

# Initialize COM in MTA mode. Required for: WIC (DirectWrite), WMF, and XInput
try:
    _ole32.CoInitializeEx(None, constants.COINIT_MULTITHREADED)
except OSError as err:
    warnings.warn("Could not set COM MTA mode. Unexpected behavior may occur.")


def _uninitialize():
    try:
        _ole32.CoUninitialize()
    except OSError:
        pass


atexit.register(_uninitialize)
