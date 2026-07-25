from __future__ import annotations
import sys
from pathlib import Path

import pyglet
from pyglet.event import EventDispatcher as _EventDispatcher, EVENT_HANDLE_STATE

"""File dialog classes for opening and saving files.

This module provides example Dialog Windows for opening and
saving files. These are made using the `tkinter` module, which
is part of the Python standard library. Dialog Windows run in a
background process to prevent any interference with your main
application, and integrate using the standard pyglet Event
framework.

Note that these dialogs do not actually open or save any data
to disk. They simply return one or more strings, which contain
the final file paths that were selected or entered. You can
then use this information in your main application to handle
the disk IO. This is done by attaching an event handler to the
dialog, which will receive the file path(s) as an argument.

Create a `FileOpenDialog` instance, and attach a handler to it::

    # Restrict to only showing ".png" and ".bmp" file types,
    # and allow selecting more than one file
    open_dialog = FileOpenDialog(filetypes=[("PNG", ".png"), ("24-bit Bitmap", ".bmp")], multiple=True)

    # Multiple filetypes can be specified in the same string as long as a space is used. Wildcards are also accepted.
    open_dialog = FileOpenDialog(filetypes=[("Images", "*.png *.bmp *.jpg")], multiple=True)

    @open_dialog.event
    def on_dialog_open(filenames):
        print("list of selected filenames:", filenames)
        # Your own code here to handle loading the file name(s).

    # Show the Dialog whenever you need. This is non-blocking:
    open_dialog.show()


The `FileSaveDialog` works similarly::

    # Add a default file extension ".sav" to the file
    save_as = FileSaveDialog(default_ext='.sav')

    @save_as.event
    def on_dialog_save(filename):
        print("FILENAMES ON SAVE!", filename)
        # Your own code here to handle saving the file name(s).

    # Show the Dialog whenever you need. This is non-blocking:
    open_dialog.show()
"""

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

class _OpenDialogMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict) -> type:
        if _is_pyglet_doc_run:
            return super().__new__(cls, name, bases, attrs)

        if pyglet.compat_platform == "win32":
            from pyglet.window.dialog.windows import WindowsFileOpenDialog  # noqa: PLC0415
            return WindowsFileOpenDialog
        if pyglet.compat_platform == "darwin":
             from pyglet.window.dialog.darwin import MacOSFileOpenDialog  # noqa: PLC0415
             return MacOSFileOpenDialog
        if pyglet.compat_platform == "linux":
            from pyglet.window.dialog.linux import TkFileOpenDialog  # noqa: PLC0415
            return TkFileOpenDialog

        return super().__new__(cls, name, bases, attrs)


class FileOpenDialog(_EventDispatcher, metaclass=_OpenDialogMeta):
    """Opens a system file dialog window for opening files.

    .. versionadded:: 3.0
    """
    def __init__(
        self, title: str="Open File", initial_dir: str | Path | None= None, initial_file: str | None=None,
            filetypes: list[tuple[str, str]] | None=None, multiple: bool=False) -> None:
        """Establish how the open file dialog will behave.

        Args:
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
                For multiple file types in the same selection, separate by a semicolon.
                For example: [("Images", ".png;.bmp")]`
            multiple: bool
                True if multiple files can be selected. Defaults to False.
        """
        self.title = title
        self.initial_dir = initial_dir
        self.filetypes = filetypes
        self.multiple = multiple
        self.initial_file = initial_file

    def open(self) -> None:
        """Open a file dialog window to select files according to the configuration."""
        raise NotImplementedError

    def on_dialog_open(self, filenames: list[str]) -> EVENT_HANDLE_STATE:
        """Event for filename choice.

        Args:
            filenames:
                The selected filename paths chosen by the user. May be empty if nothing is chosen.
        """

class _SaveDialogMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict) -> type:
        if _is_pyglet_doc_run:
            return super().__new__(cls, name, bases, attrs)

        if pyglet.compat_platform == "win32":
            from pyglet.window.dialog.windows import WindowsFileSaveDialog  # noqa: PLC0415
            return WindowsFileSaveDialog
        if pyglet.compat_platform == "darwin":
            from pyglet.window.dialog.darwin import MacOSFileSaveDialog  # noqa: PLC0415
            return MacOSFileSaveDialog
        if pyglet.compat_platform == "linux":
            from pyglet.window.dialog.linux import TkFileSaveDialog  # noqa: PLC0415
            return TkFileSaveDialog

        return super().__new__(cls, name, bases, attrs)

class FileSaveDialog(_EventDispatcher, metaclass=_SaveDialogMeta):
    """Opens a system file dialog window for saving files.

    .. versionadded:: 3.0
    """
    def __init__(self, title: str="Save As", initial_dir: str | Path | None=None, initial_file: str | None=None,
                 filetypes: list[tuple[str, str]] | None=None, default_ext: str="") -> None:
        """Establish how the save file dialog will behave.

        Args:
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
            default_ext:
                A default file extension to add to the file. This will override
                the `filetypes` list if given, but will not override a manually
                entered extension.
        """
        self.title = title
        self.initial_dir = initial_dir or Path.cwd()
        self.filetypes = filetypes
        self.initial_file = initial_file
        self.default_ext = default_ext

    def open(self) -> None:
        """Open the file dialog window to save files according to the configuration."""
        raise NotImplementedError

    def on_dialog_save(self, filename: str) -> EVENT_HANDLE_STATE:
        """Event for filename choice.

        Args:
            filename:
                The resulting filename a user input. The string may be empty if user input nothing or cancelled
                the operation.
        """
