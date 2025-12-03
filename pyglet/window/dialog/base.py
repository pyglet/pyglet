from __future__ import annotations

from abc import abstractmethod

from pyglet.event import EventDispatcher as _EventDispatcher
from pathlib import Path


class _Dialog(_EventDispatcher):
    """Dialog base class

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
        default_ext:
            A default file extension to add to the file. This will override
            the `filetypes` list if given, but will not override a manually
            entered extension.
        """
        self.title = title
        self.initial_dir = initial_dir
        self.filetypes = filetypes
        self.initial_file = initial_file
        self.default_ext = default_ext

    def open(self) -> None:
        raise NotImplementedError

    def on_dialog_save(self, filename):
        """Event for filename choice"""


FileSaveDialogBase.register_event_type('on_dialog_save')
