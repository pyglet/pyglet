from __future__ import annotations

from abc import abstractmethod
import re

from pyglet.event import EventDispatcher as _EventDispatcher
from pathlib import Path


def _split_filetype_patterns(patterns: str) -> list[str]:
    """Return individual file patterns, accepting semicolons or whitespace.

    A pattern beginning with ``.*`` is almost certainly a typo for ``*.``.
    It would otherwise create a filter that silently matches no normal files.
    """
    result = [pattern for pattern in re.split(r"[;\s]+", patterns.strip()) if pattern]
    for pattern in result:
        if pattern.startswith(".*"):
            msg = f"Invalid file type pattern {pattern!r}; use '*.{pattern[2:]}' instead."
            raise ValueError(msg)
    return result


def _validate_filetypes(filetypes: list[tuple[str, str]] | None) -> None:
    """Validate file type patterns before a platform dialog is opened."""
    if filetypes is None:
        return
    for label, patterns in filetypes:
        if not isinstance(label, str) or not isinstance(patterns, str):
            raise TypeError("Each file type must be a (str, str) tuple.")
        _split_filetype_patterns(patterns)


class _Dialog(_EventDispatcher):
    """Dialog base class.

    This base class sets up a ProcessPoolExecutor with a single
    background Process. This allows the Dialog to display in
    the background without blocking or interfering with the main
    application Process. This also limits to a single open Dialog
    at a time.
    """
    _dialog = None

    @abstractmethod
    def open(self):
        ...

    def _dispatch_event(self, future):
        raise NotImplementedError


class FileOpenDialogBase(_Dialog):
    def __init__(
        self, title: str="Open File", initial_dir: str | Path | None = None, initial_file: str | None=None,
            filetypes: list[tuple[str, str]] | None=None, multiple: bool=False,
    ):
        """Establish how the file dialog will behave.

        title:
            The Dialog Window name. Defaults to "Open File".
        initial_dir:
            The directory to start in. If a path is not given, it is up the OS to determine behavior.
            On Windows, if None is passed, it will open to the last used directory.
        initial_file:
            The filename to prepopulate with when opening. Not supported on Mac OS.
        filetypes:
            An optional list of tuples containing (name, extension) to filter by.
            If none are given, all files will be shown and selectable.
            For example: `[("PNG", ".png"), ("24-bit Bitmap", ".bmp")]`
            For multiple file types in the same selection, separate patterns with semicolons.
            For example: [("Images", "*.png;*.bmp")]`
            Whitespace-separated patterns are accepted for compatibility.
        multiple: bool
            True if multiple files can be selected. Defaults to False.
        """
        self.title = title
        self.initial_dir = initial_dir
        _validate_filetypes(filetypes)
        self.filetypes = filetypes
        self.multiple = multiple
        self.initial_file = initial_file

    def open(self):
        raise NotImplementedError

FileOpenDialogBase.register_event_type('on_dialog_open')

class FileSaveDialogBase(_Dialog):

    def __init__(self, title="Save As", initial_dir: str | Path | None=None, initial_file=None, filetypes=None, default_ext=""):
        """Establish how the save file dialog will behave.

        title:
            The Dialog Window name. Defaults to "Save As".
        initial_dir:
            The directory to start in. If a path is not given, it is up the OS to determine behavior.
            On Windows, if None is passed, it will open to the last used directory.
        initial_file:
            A default file name to be filled in. Defaults to None.
        filetypes:
            An optional list of tuples containing (name, extension) to
            filter to. If the `default_ext` argument is not given, this list
            also dictates the extension that will be added to the entered
            file name. If a list of `filetypes` are not give, you can enter
            any file name to save as.
            For example: `[("PNG", ".png"), ("24-bit Bitmap", ".bmp")]`
            For multiple file types in the same selection, separate patterns with semicolons.
            For example: `[("Images", "*.png;*.bmp")]`
            Whitespace-separated patterns are accepted for compatibility.
        default_ext:
            A default file extension to add to the file. This will override
            the `filetypes` list if given, but will not override a manually
            entered extension.
        """
        self.title = title
        self.initial_dir = initial_dir
        _validate_filetypes(filetypes)
        self.filetypes = filetypes
        self.initial_file = initial_file
        self.default_ext = default_ext

    def open(self) -> None:
        raise NotImplementedError

    def on_dialog_save(self, filename):
        """Event for filename choice"""


FileSaveDialogBase.register_event_type('on_dialog_save')
