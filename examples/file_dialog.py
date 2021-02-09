import os as _os

from concurrent.futures import ProcessPoolExecutor as _ProcessPoolExecutor

from pyglet.event import EventDispatcher as _EventDispatcher

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


class _Dialog(_EventDispatcher):
    """Dialog base class

    This base class sets up a ProcessPoolExecutor with a single
    background Process. This allows the Dialog to display in
    the background without blocking or interfering with the main
    application Process. This also limits to a single open Dialog
    at a time.
    """

    executor = _ProcessPoolExecutor(max_workers=1)
    _dialog = None

    @staticmethod
    def _open_dialog(dialog):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        return dialog.show()

    def open(self):
        future = self.executor.submit(self._open_dialog, self._dialog)
        future.add_done_callback(self._dispatch_event)

    def _dispatch_event(self, future):
        raise NotImplementedError


class FileOpenDialog(_Dialog):
    def __init__(self, title="Open File", initial_dir=_os.path.curdir, filetypes=None, multiple=False):
        """
        :Parameters:
            `title` : str
                The Dialog Window name. Defaults to "Open File".
            `initial_dir` : str
                The directory to start in.
            `filetypes` : list of tuple
                An optional list of tuples containing (name, extension) to filter by.
                If none are given, all files will be shown and selectable.
                For example: `[("PNG", ".png"), ("24-bit Bitmap", ".bmp")]`
            `multiple` : bool
                True if multiple files can be selected. Defaults to False.
        """
        from tkinter import filedialog
        self._dialog = filedialog.Open(title=title,
                                       initialdir=initial_dir,
                                       filetypes=filetypes or (),
                                       multiple=multiple)

    def _dispatch_event(self, future):
        self.dispatch_event('on_dialog_open', future.result())

    def on_dialog_open(self, filenames):
        """Event for filename choices"""


class FileSaveDialog(_Dialog):
    def __init__(self, title="Save As", initial_dir=_os.path.curdir, initial_file=None, filetypes=None, default_ext=""):
        """
        :Parameters:
            `title` : str
                The Dialog Window name. Defaults to "Save As".
            `initial_dir` : str
                The directory to start in.
            `initial_file` : str
                A default file name to be filled in. Defaults to None.
            `filetypes` : list of tuple
                An optional list of tuples containing (name, extension) to
                filter to. If the `default_ext` argument is not given, this list
                also dictactes the extension that will be added to the entered
                file name. If a list of `filetypes` are not give, you can enter
                any file name to save as.
                For example: `[("PNG", ".png"), ("24-bit Bitmap", ".bmp")]`
            `default_ext` : str
                A default file extension to add to the file. This will override
                the `filetypes` list if given, but will not override a manually
                entered extension.
        """
        from tkinter import filedialog
        self._dialog = filedialog.SaveAs(title=title,
                                         initialdir=initial_dir,
                                         initialfile=initial_file or (),
                                         filetypes=filetypes or (),
                                         defaultextension=default_ext)

    def _dispatch_event(self, future):
        self.dispatch_event('on_dialog_save', future.result())

    def on_dialog_save(self, filename):
        """Event for filename choice"""


FileOpenDialog.register_event_type('on_dialog_open')
FileSaveDialog.register_event_type('on_dialog_save')


if __name__ == '__main__':

    #########################################
    # File Save Dialog example:
    #########################################

    save_as = FileSaveDialog(initial_file="test", filetypes=[("PNG", ".png"), ("24-bit Bitmap", ".bmp")])

    @save_as.event
    def on_dialog_save(filename):
        print("FILENAMES ON SAVE!", filename)

    save_as.open()

    #########################################
    # File Open Dialog example:
    #########################################

    open_dialog = FileOpenDialog(filetypes=[("PNG", ".png"), ("24-bit Bitmap", ".bmp")], multiple=True)

    @open_dialog.event
    def on_dialog_open(filename):
        print("FILENAMES ON OPEN!", filename)

    open_dialog.open()
