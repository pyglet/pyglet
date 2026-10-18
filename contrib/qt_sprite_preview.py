"""An example sprite previewer using Qt and pyglet together.

It allows you to edit the fragment and vertex shaders, then compile them
to get a live view. Errors and success will be printed to the console. Users
running GNOME on Linux may need the --use-qt-file-dialog flag to prevent invisible
window issues. A brief feature overview is located after the license notes below.

Important license notes:

1. Libraries can use licenses which impose requirements beyond those of
   pyglet's BSD-style style license.
2. This example defaults to using PySide6 by default, but can also use
   PyQt6 due to their nearly-identical APIs.
3. PySide6 uses the LGPL license while PyQt6 uses a GPL / commercial
   dual-license approach.

To the best knowledge of the contributors, this example and derivatives
are only obligated to meet the restrictions of the LGPL because it does
not use any PyQt6-specific features. Please see the following for more
information:

* The licenses and documentation for the libraries you plan to use
* This guide for prior versions of PySide and PyQt:
  thttps://www.pythonguis.com/faq/pyqt5-vs-pyside2/

For additional certainty, please consult a legal professional.


Example features:

You can choose the current Qt binding in two ways:

1. Add PySide6 or PyQt6 as the first argument after the launch command
   when running the script in the terminal
2. Set the PYGLET_QT_BACKEND environment variable to either PySide6 or
   PyQt6.

The priority order is:

1. positional argument
2. environment variable
3. default to PySide6

To load images, choose File -> Open Image.

Images loaded will be listed in the Images menu. By selecting an image in
the menu list, it will be unloaded. Names in parentheses will be used for
the sampler2D name. Each layer supplies a vertex attribute named
<sampler_name>_coords (for example, sprite_texture0_coords).
The default shaders combine two images. When changing the image count, update
the shaders to declare and use each loaded layer's coordinates and sampler.

You can open a shader (both vert and frag) at the same time. Text is
allowed, but will load into the fragment shader. Saving a shader saves
both frag and vertex (IE: test becomes test.vert and test.frag)

Scrolling the mousewheel also zooms in.
"""
from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Final

import pyglet
from pyglet.graphics.api.gl import ExternalOpenGLContext
from pyglet.graphics.api.gl.gl_info import GLInfo
from pyglet.window.camera import Camera2D

# Constants for choosing a Qt backend and summarizing their licensing
ENV_VARIABLE: Final[str] = 'PYGLET_QT_BACKEND'

PYSIDE6: Final[str] = 'PySide6'
PYQT6: Final[str] = 'PyQt6'

valid_backends: Final[dict[str, str]] = {
    PYSIDE6: "LGPL; may allow releasing under non-GPL licenses",
    PYQT6: "Dual GPL / Commercial license; requires GPL or a fee",
}

# Default to PySide6 as part of allowing non-GPL licenses
# This is necessary but not sufficient to allow this.
DEFAULT: Final[str] = PYSIDE6


# Argument parser for run-time config as __main__
parser = argparse.ArgumentParser(
    description=dedent("""\
    A sprite & shader previewer using Qt and pyglet together.

    It defaults to PySide6, but can run on PyQt6. The details of how may
    be helpful to users who want to avoid spreading PyQt6's GPL license
    while using it as a fallback. See the docstrings and comments in the
    source to learn more.
    """),
    formatter_class=argparse.RawTextHelpFormatter)

# On Python 3.9+, argparse.BooleanOptionalAction is more concise
# See https://docs.python.org/3.9/library/argparse.html#action
parser.add_argument(
    '--use-qt-file-dialog', dest='native_file_dialog', action='store_false',
    help="Use Qt's file chooser instead of the system's. Helpful on Gnome DE.",
)
parser.set_defaults(native_file_dialog=True)


# Generate options help text lines
backend_column_width: Final[int] = max(map(len, valid_backends))
help_lines: list[str] = ["Which Qt binding to use.\n"]

for backend, description in valid_backends.items():
   line_parts = [
       f"{backend: <{backend_column_width}} - ",
       '(Default) ' if backend == DEFAULT else '',
       description,
   ]
   help_lines.append(''.join(line_parts))

# Add an optional single-value positional argument
parser.add_argument('backend', nargs='?',
    choices=valid_backends.keys(),
    help='\n'.join(help_lines))


# Use the 1st non-None Qt binding value: argument, env var, or default
arguments = None
if __name__ == "__main__":
    arguments = parser.parse_args()

reasons_with_backend_values: Final[dict[str, str | None]] = {
   'first positional argument'       : None if not arguments else arguments.backend,
   # An environment variable allows specifying the binding when
   # importing the module instead of running it as a main program.
   f'{ENV_VARIABLE!r} env variable'  : os.environ.get(ENV_VARIABLE, None),
   'default'                         : DEFAULT,
}
reason, backend = next(filter(
    lambda t: t[1] is not None, reasons_with_backend_values.items()))

print(f"Selected {backend} as the Qt binding from the {reason}'s value.")



# Use PySide6 for type checking, static analysis, tests, and linting
# to help avoid infection by PyQt6's GPL license since tools will mark
# uses of PyQt6-specific features as missing. For example, pyright is
# one of the strict type checking and linting tools which can help.
if TYPE_CHECKING or backend == PYSIDE6:
    from PySide6 import QtCore, QtWidgets, QtGui
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtWidgets import QFileDialog
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

elif backend == PYQT6:
    from PyQt6 import QtCore, QtWidgets, QtGui
    from PyQt6.QtGui import QWheelEvent
    from PyQt6.QtWidgets import QFileDialog
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget

else:  # Handle import edge cases
    raise ValueError(
        f"Expected a value in {valid_backends},"
        f" but got {backend!r} via {reason}")

# Import the other constants after the UI libraries to avoid
# cluttering the symbol table when debugging import problems.

default_vertex_src = """#version 150 core
in vec3 translate;
in vec4 colors;
in vec3 sprite_texture0_coords;
in vec3 sprite_texture1_coords;
in vec2 scale;
in vec3 position;
in float rotation;

out vec4 vertex_colors;
out vec3 texture_coords;
out vec3 texture_coords1;

uniform WindowBlock
{
    mat4 projection;
    mat4 view;
} window;

mat4 m_scale = mat4(1.0);
mat4 m_rotation = mat4(1.0);
mat4 m_translate = mat4(1.0);

void main()
{
    m_scale[0][0] = scale.x;
    m_scale[1][1] = scale.y;
    m_translate[3][0] = translate.x;
    m_translate[3][1] = translate.y;
    m_translate[3][2] = translate.z;
    m_rotation[0][0] =  cos(-radians(rotation)); 
    m_rotation[0][1] =  sin(-radians(rotation));
    m_rotation[1][0] = -sin(-radians(rotation));
    m_rotation[1][1] =  cos(-radians(rotation));

    gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

    vertex_colors = colors;
    texture_coords = sprite_texture0_coords;
    texture_coords1 = sprite_texture1_coords;
}
"""

default_frag_src = """#version 150 core
in vec4 vertex_colors;
in vec3 texture_coords;
in vec3 texture_coords1;
out vec4 final_colors;

uniform sampler2D sprite_texture0;
uniform sampler2D sprite_texture1;
uniform float time;

void main()
{
    vec2 uv = texture_coords.xy;
    vec3 col = 0.5 + 0.5 * cos(time + uv.xyx + vec3(0, 2, 4));

    final_colors = texture(sprite_texture1, texture_coords1.xy) * texture(sprite_texture0, uv) * vertex_colors * vec4(col, 1.0);
}"""

class Ui_MainWindow:
    program: pyglet.graphics.ShaderProgram | None
    sprite: pyglet.sprite.MultiTextureSprite | None
    SPRITE_POSITION = (0, 0)

    def __init__(self, use_native_file_dialog: bool = True):
        self.use_native_file_dialog: bool = use_native_file_dialog

        self.images = []

        self.group = pyglet.graphics.Group()

        self.sprite = None
        self.program = None

    def get_file_dialog_options(self) -> QFileDialog.Option:
        """Convert instance attributes to a file dialog options object.

        At the moment, it supports choosing which dialog to use. This is
        helpful on certain Gnome and tiling Linux desktop configurations
        which can have issues with the system file picker.

        You may want to expand on this in your own application with
        additional options.
        """
        options = QFileDialog.Option()
        if not self.use_native_file_dialog:
            options |= QFileDialog.Option.DontUseNativeDialog

        return options

    def setupUi(self, MainWindow: QtWidgets.QMainWindow) -> None:
        self._window = MainWindow

        # Set up the central window widget object
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(820, 855)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Create layout for shader editing
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading
            | QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.vertex_source_edit = QtWidgets.QTextEdit(self.centralwidget)
        self.vertex_source_edit.setAcceptRichText(False)
        self.vertex_source_edit.setObjectName("vertex_source_edit")
        self.verticalLayout.addWidget(self.vertex_source_edit)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.fragSourceEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.fragSourceEdit.setAcceptRichText(False)
        self.fragSourceEdit.setObjectName("frag_source_edit")
        self.verticalLayout_2.addWidget(self.fragSourceEdit)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.compileShaderBtn = QtWidgets.QPushButton(self.centralwidget)
        self.compileShaderBtn.clicked.connect(self.compileClick)
        self.compileShaderBtn.setObjectName("compile_shader_btn")
        self.verticalLayout_3.addWidget(self.compileShaderBtn)

        # Initialize the pyglet widget we'll draw to and lay out the window
        self.openGLWidget = PygletWidget(800, 400, self.centralwidget, self)
        self.openGLWidget.setMinimumSize(QtCore.QSize(800, 400))
        self.openGLWidget.setObjectName("openGLWidget")
        self.verticalLayout_3.addWidget(self.openGLWidget)
        self.gridLayout.addLayout(self.verticalLayout_3, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)

        # Set up the root top menu & status bar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 820, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        # Add menu bar menus, entries, and hotkeys
        self.actionOpen_Image = QtGui.QAction(MainWindow)
        self.actionOpen_Image.setObjectName("actionOpen_Image")
        self.actionOpen_Image.triggered.connect(self.loadImages)
        self.actionOpen_Image.setShortcut("Ctrl+I")

        self.actionOpen_Shader = QtGui.QAction(MainWindow)
        self.actionOpen_Shader.setObjectName("actionOpen_Shader")
        self.actionOpen_Shader.triggered.connect(self.loadShaders)
        self.actionOpen_Shader.setShortcut("Ctrl+O")

        self.actionSave_Shader = QtGui.QAction(MainWindow)
        self.actionSave_Shader.setObjectName("actionSave_Shader")
        self.actionSave_Shader.triggered.connect(self.saveShaders)
        self.actionSave_Shader.setStatusTip('Saves both Shader Files')
        self.actionSave_Shader.setShortcut("Ctrl+S")

        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.triggered.connect(self.closeProgram)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionOpen_Image)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionOpen_Shader)
        self.menuFile.addAction(self.actionSave_Shader)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.imageMenu = QtWidgets.QMenu(self.menubar)
        self.imageMenu.setObjectName("imageMenu")
        self.noImageAction = QtGui.QAction(MainWindow)
        self.noImageAction.setDisabled(True)
        self.imageMenu.addAction(self.noImageAction)

        self.menubar.addAction(self.imageMenu.menuAction())

        # Perform localization & start accepting UI events
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def compileClick(self) -> None:
        if not self.images:
            print("No images have been loaded.")
            return

        self.openGLWidget.pyglet_context.set_current()

        if self.sprite:
            self.sprite.delete()
            self.sprite = None

        if self.program:
            del self.program
            self.program = None

        try:
            vertex_ = pyglet.graphics.Shader(self.vertex_source_edit.toPlainText(), 'vertex')
            fragment_ = pyglet.graphics.Shader(self.fragSourceEdit.toPlainText(), 'fragment')

            self.program = pyglet.graphics.ShaderProgram(
                vertex_, fragment_, vertex_layout=pyglet.graphics.VertexLayout(colors="4Bn"))

            images = {image.shader_name: image for image in self.images}
            self.sprite = pyglet.sprite.MultiTextureSprite(
                images,
                x=self.SPRITE_POSITION[0], y=self.SPRITE_POSITION[1],
                group=self.group, batch=self.openGLWidget.batch,
                program=self.program)

            if self.program:
                print("Successfully compiled shader.")
        except pyglet.graphics.shader.ShaderException as err:
            print(f"Failed to compile shader: {err}")

    def loadImages(self) -> None:
        options = self.get_file_dialog_options()
        fileNames, _ = QFileDialog.getOpenFileNames(
            self._window, "Select Image Files", "", "Image Files (*.png *.jpg *.jpeg *.bmp)",
            options=options)

        for fileName in fileNames:
            if not self.images:
                self.imageMenu.removeAction(self.noImageAction)

            action = QtGui.QAction(self._window)
            shader_name = f"sprite_texture{len(self.images)}"
            action.setText(f"{os.path.basename(fileName)} ({shader_name})")
            action.fileName = fileName
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(lambda checked=False, action=action: self.removeImage(action))
            image = pyglet.image.load(fileName)
            image.shader_name = shader_name
            action.image = image
            self.images.append(image)
            self.imageMenu.addAction(action)

    def loadShaders(self) -> None:
        options = self.get_file_dialog_options()
        file_names, _ = QFileDialog.getOpenFileNames(
            self._window, "Load Shader Files", "", "Shader Files (*.vert *.frag *.txt)",
            options=options)

        for file_name in file_names:
            file_path = Path(file_name)
            ext = file_path.suffixes[-1]

            if ext == '.vert':
                dest = self.vertex_source_edit
            elif ext in ('.txt', '.frag'):
                dest = self.fragSourceEdit
            else:
                dest = self.fragSourceEdit

            text = file_path.read_text()
            dest.setText(text)

    def saveShaders(self) -> None:
        options = self.get_file_dialog_options()
        file_name, _ = QFileDialog.getSaveFileName(
            self._window, "Saving Both Shader Files (vert and frag)", "",
            options=options)

        if file_name:
            base_path = Path(file_name)
            vert_filename = base_path.with_suffix(".vert")
            frag_filename = base_path.with_suffix(".frag")

            vert_filename.write_text(self.vertex_source_edit.toPlainText())
            frag_filename.write_text(self.fragSourceEdit.toPlainText())

    def removeImage(self, actionWidget: QtGui.QAction) -> None:
        if self.imageMenu:
            self.imageMenu.removeAction(actionWidget)

            self.images.remove(actionWidget.image)

            # Re-order shader names
            for idx, image in enumerate(self.images):
                image.shader_name = f"sprite_texture{idx}"

            for action in self.imageMenu.actions():
                shader_name = action.image.shader_name
                action.setText(f"{os.path.basename(action.fileName)} ({shader_name})")

            if len(self.images) == 0:
                self.imageMenu.addAction(self.noImageAction)

    def closeProgram(self) -> None:
        app.exit()

    def retranslateUi(self, MainWindow: QtWidgets.QMainWindow) -> None:
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Sprite Shader Previewer"))
        self.label.setText(_translate("MainWindow", "Vertex Source:"))
        self.label_2.setText(_translate("MainWindow", "Fragment Source:"))
        self.compileShaderBtn.setText(_translate("MainWindow", "Compile Shaders"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen_Image.setText(_translate("MainWindow", "Open Images"))
        self.actionOpen_Shader.setText(_translate("MainWindow", "Open Shader"))
        self.actionSave_Shader.setText(_translate("MainWindow", "Save Shader"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.imageMenu.setTitle(_translate("MainWindow", "Images"))
        self.noImageAction.setText(_translate("MainWindow", "No Images Loaded"))

        self.vertex_source_edit.setText(default_vertex_src)
        self.fragSourceEdit.setText(default_frag_src)


class QtWindowWrapper(pyglet.event.EventDispatcher):
    """Bridge Qt window data and resize notifications to pyglet cameras."""

    def __init__(self, widget: QOpenGLWidget, context: ExternalOpenGLContext) -> None:
        self.widget = widget
        self.context = context
        self.camera = Camera2D(self, min_zoom=0.125, max_zoom=40.0)
        self.context.camera = self.camera

    def get_size(self) -> tuple[int, int]:
        return self.widget.width(), self.widget.height()

    def get_framebuffer_size(self) -> tuple[int, int]:
        ratio = self.widget.devicePixelRatioF()
        return int(self.widget.width() * ratio), int(self.widget.height() * ratio)

    def close(self) -> None:
        """Release the owned camera while the graphics context is current."""
        self.context.camera = None
        self.remove_handlers(self.camera)
        self.camera.delete()


QtWindowWrapper.register_event_type('_on_internal_resize')
QtWindowWrapper.register_event_type('_on_internal_scale')


class PygletWidget(QOpenGLWidget):
    def __init__(self, width, height, parent, mainWindow) -> None:
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setMinimumSize(width, height)
        self._cleaned_up = True
        QtWidgets.QApplication.instance().aboutToQuit.connect(self.cleanup)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._pyglet_update)
        self.timer.setInterval(0)
        self._window_wrapper: QtWindowWrapper | None = None
        self.elapsed = 0

    def wheelEvent(self, event: QWheelEvent) -> None:
        super().wheelEvent(event)
        if self._window_wrapper is None:
            return
        if event.angleDelta().y() > 0:
            self._window_wrapper.camera.zoom *= 2
        else:
            self._window_wrapper.camera.zoom /= 2
        event.accept()

    def advance_time(self, dt: float) -> None:
        self.elapsed += dt

    def _pyglet_update(self) -> None:
        # Clock callbacks update CPU state; GPU writes happen during paintGL.
        pyglet.clock.tick()
        self.update()

    def paintGL(self) -> None:
        """Render with the camera while pyglet's context and frame are active."""
        with self.pyglet_context.frame():
            self.pyglet_context.clear()
            program = self.mainWindow.program
            if program is not None and 'time' in program.uniforms:
                with program:
                    program['time'] = self.elapsed
            self.batch.draw()

    def resizeGL(self, width: int, height: int) -> None:
        if self._window_wrapper is not None:
            self._window_wrapper.dispatch_event('_on_internal_resize', width, height)

    def initializeGL(self) -> None:
        """Create GPU resources after Qt has created the native context."""
        self.pyglet_context = ExternalOpenGLContext(
            make_current=self.makeCurrent,
            is_current=lambda: QtGui.QOpenGLContext.currentContext() == self.context(),
            get_proc_address=lambda name: self.context().getProcAddress(name),
            get_framebuffer=self.defaultFramebufferObject,
        )
        self.pyglet_context.set_current()
        # Query Qt's context for info.
        self.gl_info = GLInfo(platform_info=None)
        self.gl_info.query(self.pyglet_context)
        print(f"Qt OpenGL Version: {self.gl_info.version}, renderer: {self.gl_info.renderer}")
        self.context().aboutToBeDestroyed.connect(self.cleanup)
        self.batch = pyglet.graphics.Batch()
        self._window_wrapper = QtWindowWrapper(self, self.pyglet_context)
        self.resizeGL(self.width(), self.height())
        self._cleaned_up = False
        self.timer.start()
        pyglet.clock.schedule_interval(self.advance_time, 1 / 60.0)

    def cleanup(self) -> None:
        """Release GPU resources before Qt destroys its native context."""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self.timer.stop()
        pyglet.clock.unschedule(self.advance_time)
        self.pyglet_context.set_current()
        if self.mainWindow.sprite:
            self.mainWindow.sprite.delete()
            self.mainWindow.sprite = None
        if self.mainWindow.program:
            self.mainWindow.program.delete()
            self.mainWindow.program = None
        self._window_wrapper.close()
        self._window_wrapper = None
        self.pyglet_context.destroy()



def excepthook(exc_type, exc_value, exc_tb) -> None:
    """Replacement for Python's default exception handler function.

    See the following for more information:
    https://docs.python.org/3/library/sys.html#sys.excepthook
    """
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb)


if __name__ == "__main__":
    # Create the base Qt application and initialize the UI
    app = QtWidgets.QApplication(sys.argv)
    ui = Ui_MainWindow(use_native_file_dialog=arguments.native_file_dialog)
    qt_window = QtWidgets.QMainWindow()
    ui.setupUi(qt_window)
    qt_window.show()

    # Replace the default exception handling *after* everything is
    # initialized to avoid swallowing fatal errors such as GL issues.
    sys.excepthook = excepthook

    # Start the application and return its exit code
    sys.exit(app.exec())
