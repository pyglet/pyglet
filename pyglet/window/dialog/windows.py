from __future__ import annotations

import ctypes
import threading
from pathlib import Path

from _ctypes import sizeof
from ctypes import create_unicode_buffer

import pyglet
from pyglet.libs.win32 import OPENFILENAMEW, _comdlg32
from pyglet.libs.win32.constants import (
    OFN_EXPLORER,
    OFN_PATHMUSTEXIST,
    OFN_OVERWRITEPROMPT,
    OFN_FILEMUSTEXIST,
    OFN_ALLOWMULTISELECT,
)
from pyglet.window.dialog.base import FileOpenDialogBase, FileSaveDialogBase


def _build_filter_string(filetypes: list[tuple[str, str]]) -> str:
    """Create filter string for filetypes.

    Args:
        filetypes:
            e.g. [("PNG", "*.png"), ("24-bit Bitmap", "*.bmp"), ("Images", "*.png;*.bmp"]
    """
    parts: list[str] = []

    for label, exts in filetypes:
        # Normalize to a list
        if isinstance(exts, str):
            exts = [exts]

        norm_patterns: list[str] = []
        for ext in exts:
            ext = ext.strip()
            if not ext:
                continue
            if ext.startswith("*."):
                pass  # already "*.png"
            elif ext.startswith("."):  # Just incase, add * if someone didn't add.
                ext = "*" + ext  # ".png" -> "*.png"
            else:
                ext = "*." + ext  # "png"  -> "*.png"
            norm_patterns.append(ext)

        if not norm_patterns:
            pattern_str = "*.*"
        else:
            pattern_str = ";".join(norm_patterns)

        # Add pattern to the label.
        display_label = f"{label} ({pattern_str})"

        parts.append(display_label)
        parts.append(pattern_str)

    # Join pairs with single nulls and end with double null
    return "\0".join(parts) + "\0\0"


def _parse_multiselect(buffer) -> list[str]:
    text = buffer[:]

    # Split on nulls
    parts = text.split("\0")

    # Remove empty entries
    parts = [p for p in parts if p]

    if not parts:
        return []

    # If only 1 part → it's a single file
    if len(parts) == 1:
        return [parts[0]]

    # otherwise:
    folder = parts[0]
    files = parts[1:]

    return [folder + "\\" + f for f in files]


def _build_ofn(hwnd, title, initialdir, initial_file, filetypes, multiple, for_save=False, buffer_chars=65536, default_ext=None,
    ):
        file_buffer = create_unicode_buffer(buffer_chars)

        if initial_file:
            file_buffer.value = initial_file

        filter_str = _build_filter_string(filetypes) if filetypes else None

        ofn = OPENFILENAMEW()
        ofn.lStructSize = sizeof(ofn)
        ofn.hwndOwner = hwnd
        ofn.lpstrFilter = filter_str
        ofn.nFilterIndex = 1

        ofn.lpstrFile = ctypes.cast(file_buffer, ctypes.c_wchar_p)
        ofn.nMaxFile = buffer_chars

        # Optional fields
        ofn.lpstrFileTitle = None
        ofn.nMaxFileTitle = 0
        if isinstance(initialdir, Path):
            initialdir = initialdir.absolute()
        ofn.lpstrInitialDir = str(initialdir)
        ofn.lpstrTitle = title

        # Base flags
        flags = OFN_EXPLORER

        if for_save:
            flags |= OFN_PATHMUSTEXIST | OFN_OVERWRITEPROMPT
        else:
            flags |= OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST

        if multiple and not for_save:
            flags |= OFN_ALLOWMULTISELECT

        ofn.Flags = flags

        # Default extension for save dialog (optional)
        if for_save and default_ext:
            # strip leading dot
            if default_ext.startswith("."):
                default_ext = default_ext[1:]
            ofn.lpstrDefExt = default_ext

        return ofn, file_buffer


class WindowsFileOpenDialog(FileOpenDialogBase):

    def _open_dialog(self) -> list[str] | None:
        ofn, file_buffer = _build_ofn(
            hwnd=None,
            title=self.title,
            initialdir=self.initial_dir,
            initial_file=self.initial_file,
            filetypes=self.filetypes,
            multiple=self.multiple,
            for_save=False,
            buffer_chars=65536,
        )

        if not _comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
            return None

        if self.multiple:
            return _parse_multiselect(file_buffer.value)

        return file_buffer.value

    def open(self) -> None:
        def run() -> None:
            result = self._open_dialog()
            if result is None:
                result = []
            assert isinstance(result, list)
            pyglet.app.platform_event_loop.post_event(self, "on_dialog_open", result)

        threading.Thread(target=run, daemon=True).start()



class WindowsFileSaveDialog(FileSaveDialogBase):
    def _open_dialog(self) -> str:
        ofn, file_buffer = _build_ofn(
            hwnd=None,
            title=self.title,
            initialdir=self.initial_dir,
            initial_file=self.initial_file,
            filetypes=self.filetypes,
            multiple=False,
            for_save=True,
            buffer_chars=65536,
            default_ext=self.default_ext,
        )

        if not _comdlg32.GetSaveFileNameW(ctypes.byref(ofn)):
            return ""

        return file_buffer.value

    def open(self) -> None:
        def run() -> None:
            result = self._open_dialog()
            pyglet.app.platform_event_loop.post_event(self, "on_dialog_save", result)

        threading.Thread(target=run, daemon=True).start()
