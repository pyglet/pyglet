"""An example sprite previewer using Qt and pyglet together.

It allows you to edit the fragment and vertex shaders, then compile them
to get a live view. Errors and success will be printed to the console.
A brief feature overview is located after the license notes below.


Important license notes:

1. Libraries can use licenses which impose requirements beyond those of
   pyglet's BSD-style style license.
2. This example defaults to using PySide2 by default, but can also use
   PyQt5 due to their nearly-identical APIs.
3. PySide2 uses the LGPL license while PyQt5 uses a GPL / commercial
   dual-license approach.

To the best knowledge of the contributors, this example and derivatives
are only obligated to meet the restrictions of the LGPL because it does
not use any PyQt5-specific features. Please see the following for more
information:

* The licenses and documentation for the libraries you plan to use
* https://www.pythonguis.com/faq/pyqt5-vs-pyside2/

If you need additional certainty, please consult a legal professional.


Example features:

You can choose the current Qt binding in two ways:

1. Add PySide2 or PyQt5 as the first argument after the launch command
   when running the script in the terminal
2. Set the PYGLET_QT_BACKEND environment variable to either PySide2 or
   PyQt5.

The priority order is:

1. positional argument
2. environment variable
3. default to PySide2

To load images, choose File -> Open Image.

Images loaded will be listed in the Images menu. By selecting an image in
the menu list, it will be unloaded. Names in parentheses will be used for
the sampler2D name.

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
from typing import TYPE_CHECKING, Final, Mapping

# Constants for choosing a Qt backend and summarizing their licensing
ENV_VARIABLE: Final[str] = 'PYGLET_QT_BACKEND'

PYSIDE2: Final[str] = 'PySide2'
PYQT5: Final[str] = 'PyQt5'

valid_backends: Final[dict[str, str]] = {
    PYSIDE2: "LGPL; may allow releasing under non-GPL licenses",
    PYQT5: "Dual GPL / Commercial license; requires GPL or a fee",
}

# Default to PySide2 as part of allowing non-GPL licenses
# This is necessary but not sufficient to allow this.
DEFAULT: Final[str] = PYSIDE2


# Argument parser for run-time config as __main__
parser = argparse.ArgumentParser(
    description=dedent("""\
    A sprite & shader previewer using Qt and pyglet together.

    It defaults to PySide2, but can run on PyQt5. The details of how may
    be helpful to users who want to avoid spreading PyQt5's GPL license
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


# Perform UI imports according to the detected configuration
import pyglet

# Use PySide2 for type checking, static analysis, tests, and linting
# to help avoid infection by PyQt5's GPL license since tools will mark
# uses of PyQt5-specific features as missing. For example, pyright is
# one of the strict type checking and linting tools which can help.
if TYPE_CHECKING or backend == PYSIDE2:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtGui import QWheelEvent
    from PySide2.QtWidgets import QFileDialog, QOpenGLWidget

elif backend == PYQT5:
    from PyQt5 import QtCore, QtWidgets
    from PyQt5.QtGui import QWheelEvent
    from PyQt5.QtWidgets import QFileDialog, QOpenGLWidget

else:  # Handle import edge cases
    raise ValueError(
        f"Expected a value in {valid_backends},"
        f" but got {backend!r} via {reason}")

# Import the other constants after the UI libraries to avoid
# cluttering the symbol table when debugging import problems.
from pyglet.gl import (
   GL_BLEND,
   GL_COLOR_BUFFER_BIT,
   GL_DEPTH_BUFFER_BIT,
   GL_TEXTURE0,
   glActiveTexture,
   glBindTexture,
   glBlendFunc,
   glClear,
   glDisable,
   glEnable,
)

default_vertex_src = """#version 150 core
in vec3 translate;
in vec4 colors;
in vec3 tex_coords;
in vec2 scale;
in vec3 position;
in float rotation;

out vec4 vertex_colors;
out vec3 texture_coords;

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
    texture_coords = tex_coords;
}
"""

default_frag_src = """#version 150 core
in vec4 vertex_colors;
in vec3 texture_coords;
out vec4 final_colors;

uniform sampler2D sprite_texture0;
uniform sampler2D sprite_texture1;
uniform float time;

void main()
{
    vec2 uv = texture_coords.xy;
    vec3 col = 0.5 + 0.5 * cos(time + uv.xyx + vec3(0, 2, 4));
    
    final_colors = texture(sprite_texture1, uv) * texture(sprite_texture0, uv) * vertex_colors * vec4(col, 1.0);
}"""


class MultiTextureSpriteGroup(pyglet.sprite.SpriteGroup):
    """A sprite group which uses multiple textures and samplers."""

    def __init__(
            self,
            textures: Mapping[str, pyglet.image.Texture],
            blend_src: int,
            blend_dest: int,
            program: pyglet.graphics.shader.ShaderProgram | None = None,
            parent: pyglet.graphics.Group | None = None,
    ) -> None:
        """Create a sprite group for multiple textures and samplers.

        All textures must share the same target type.

        :Parameters:
            `textures` :
                 A mapping of sampler names to texture data.
            `blend_src` :
                OpenGL blend source mode; for example,
                ``GL_SRC_ALPHA``.
            `blend_dest` :
                OpenGL blend destination mode; for example,
                ``GL_ONE_MINUS_SRC_ALPHA``.
            `parent` :
                Optional parent group.
        """
        self.images = textures
        texture = list(self.images.values())[0]
        self.target = texture.target
        super().__init__(texture, blend_src, blend_dest, program, parent)

        self.program.use()
        for idx, name in enumerate(self.images):
            try:
                self.program[name] = idx
            except pyglet.graphics.shader.ShaderException as e:
                print(e)

        self.program.stop()

    def set_state(self) -> None:
        self.program.use()

        for i, texture in enumerate(self.images.values()):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(self.target, texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()
        glActiveTexture(GL_TEXTURE0)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.texture!r}-{int(self.texture.id)})'

    def __eq__(self, other) -> bool:
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.images == other.textures and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self) -> int:
        return hash((id(self.parent),
                     id(self.images),
                     self.blend_src, self.blend_dest))


class MultiTextureSprite(pyglet.sprite.Sprite):

    def __init__(
            self,
            imgs: Mapping[str, pyglet.image.Texture],
            x: float = 0, y: float = 0, z: float = 0,
            blend_src: int = pyglet.gl.GL_SRC_ALPHA,
            blend_dest: int = pyglet.gl.GL_ONE_MINUS_SRC_ALPHA,
            batch: pyglet.graphics.Batch | None = None,
            group: MultiTextureSpriteGroup | None = None,
            subpixel: bool = False,
            program: pyglet.graphics.shader.ShaderProgram = None,
    ) -> None:

        self._x = x
        self._y = y
        self._z = z

        self._texture = list(imgs.values())[0]

        if isinstance(self._texture, pyglet.image.TextureArrayRegion):
            self._program = program or pyglet.sprite.get_default_array_shader()
        else:
            self._program = program or pyglet.sprite.get_default_shader()

        self._batch = batch or pyglet.graphics.get_default_batch()

        self._group = MultiTextureSpriteGroup(imgs, blend_src, blend_dest, self.program, group)

        self._subpixel = subpixel
        self._create_vertex_list()


class Ui_MainWindow:
    SPRITE_POSITION = (0, 0)

    def __init__(self, use_native_file_dialog: bool = True):
        self.use_native_file_dialog: bool = use_native_file_dialog

        self.images = []

        self.group = pyglet.graphics.Group()

        self.sprite = None
        self.program = None

    def get_file_dialog_options(self) -> QFileDialog.Options:
        """Convert instance attributes to a file dialog options object.

        At the moment, it supports choosing which dialog to use. This is
        helpful on certain Gnome and tiling Linux desktop configurations
        which can have issues with the system file picker.

        You may want to expand on this in your own application with
        additional options.
        """
        options = QFileDialog.Options()
        if not self.use_native_file_dialog:
            options |= QFileDialog.DontUseNativeDialog

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
        self.label.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
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
        self.actionOpen_Image = QtWidgets.QAction(MainWindow)
        self.actionOpen_Image.setObjectName("actionOpen_Image")
        self.actionOpen_Image.triggered.connect(self.loadImages)
        self.actionOpen_Image.setShortcut("Ctrl+I")

        self.actionOpen_Shader = QtWidgets.QAction(MainWindow)
        self.actionOpen_Shader.setObjectName("actionOpen_Shader")
        self.actionOpen_Shader.triggered.connect(self.loadShaders)
        self.actionOpen_Shader.setShortcut("Ctrl+O")

        self.actionSave_Shader = QtWidgets.QAction(MainWindow)
        self.actionSave_Shader.setObjectName("actionSave_Shader")
        self.actionSave_Shader.triggered.connect(self.saveShaders)
        self.actionSave_Shader.setStatusTip('Saves both Shader Files')
        self.actionSave_Shader.setShortcut("Ctrl+S")

        self.actionExit = QtWidgets.QAction(MainWindow)
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
        self.noImageAction = QtWidgets.QAction(MainWindow)
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

        self.openGLWidget.makeCurrent()

        if self.sprite:
            self.sprite.delete()
            self.sprite = None

        if self.program:
            del self.program
            self.program = None

        try:
            vertex_ = pyglet.graphics.shader.Shader(self.vertex_source_edit.toPlainText(), 'vertex')
            fragment_ = pyglet.graphics.shader.Shader(self.fragSourceEdit.toPlainText(), 'fragment')

            self.program = pyglet.graphics.shader.ShaderProgram(vertex_, fragment_)

            if len(self.images) == 1:
                self.sprite = pyglet.sprite.Sprite(
                    self.images[0],
                    x=self.SPRITE_POSITION[0], y=self.SPRITE_POSITION[1],
                    group=self.group, batch=self.openGLWidget.batch,
                    program=self.program)
            else:
                textures = {image.shader_name: image.get_texture() for image in self.images}
                self.sprite = MultiTextureSprite(
                    textures,
                    x=self.SPRITE_POSITION[0], y=self.SPRITE_POSITION[1],
                    group=self.group, batch=self.openGLWidget.batch,
                    program=self.program)

            if self.program:
                print("Successfully compiled shader.")
        except pyglet.gl.lib.GLException as err:
            print(f"Failed to compile shader: {err}")
        except Exception as err:
            print("Unexpected error", err)
    def loadImages(self) -> None:
        options = self.get_file_dialog_options()
        fileNames, _ = QFileDialog.getOpenFileNames(
            self._window, "Select Image Files", "", "Image Files (*.png *.jpg *.jpeg *.bmp)",
            options=options)

        for fileName in fileNames:
            if not self.images:
                self.imageMenu.removeAction(self.noImageAction)

            action = QtWidgets.QAction(self._window)
            shader_name = f"sprite_texture{len(self.images)}"
            action.setText(f"{os.path.basename(fileName)} ({shader_name})")
            action.fileName = fileName
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(lambda: self.removeImage(action))
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

    def removeImage(self, actionWidget: QtWidgets.QAction) -> None:
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


class PygletWidget(QOpenGLWidget):
    _default_vertex_source = """#version 150 core
        in vec4 position;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        void main()
        {
            gl_Position = window.projection * window.view * position;
        }
    """
    _default_fragment_source = """#version 150 core
        out vec4 color;

        void main()
        {
            color = vec4(1.0, 0.0, 0.0, 1.0);
        }
    """

    def __init__(self, width, height, parent, mainWindow) -> None:
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setMinimumSize(width, height)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._pyglet_update)
        self.timer.setInterval(0)
        self.timer.start()

        self.zoom = 1.0

        self.elapsed = 0

        pyglet.clock.schedule_interval(self.update_time_uniform, 1 / 60.0)

    def wheelEvent(self, event: QWheelEvent) -> None:
        super().wheelEvent(event)
        if event.angleDelta().y() > 0:
            self.zoom *= 2
        else:
            self.zoom /= 2

        self.zoom = pyglet.math.clamp(self.zoom, 0.125, 40.0)
        self.view = pyglet.math.Mat4().scale(pyglet.math.Vec3(
            self.zoom, self.zoom, 1.0))

        event.accept()

    def update_time_uniform(self, dt: float) -> None:
        self.elapsed += dt

        if self.mainWindow.program:
            self.mainWindow.program.use()

            # Ignore time if it doesn't exist.
            try:
                self.mainWindow.program['time'] = self.elapsed
            except Exception:
                pass

            self.mainWindow.program.stop()

    def _pyglet_update(self) -> None:
        # Tick the pyglet clock, so scheduled events can work.
        pyglet.clock.tick()

        # Force widget to update, otherwise paintGL will not be called.
        self.update()  # self.updateGL() for pyqt5

    def paintGL(self) -> None:
        """Pyglet equivalent of on_draw event for window"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.batch.draw()

    def resizeGL(self, width: int, height: int) -> None:
        self.projection = pyglet.math.Mat4.orthogonal_projection(0, width, 0, height, -255, 255)

        self.viewport = 0, 0, width, height

    def initializeGL(self) -> None:
        """Call anything that needs a context to be created."""
        self._projection_matrix = pyglet.math.Mat4()
        self._view_matrix = pyglet.math.Mat4()

        self.batch = pyglet.graphics.Batch()

        self._default_program = pyglet.graphics.shader.ShaderProgram(
            pyglet.graphics.shader.Shader(self._default_vertex_source, 'vertex'),
            pyglet.graphics.shader.Shader(self._default_fragment_source, 'fragment'))

        self.ubo = self._default_program.uniform_blocks['WindowBlock'].create_ubo()

        self.view = pyglet.math.Mat4()
        self.projection = pyglet.math.Mat4.orthogonal_projection(0, self.width(), 0, self.height(), -255, 255)
        self.viewport = 0, 0, self.width(), self.height()

    @property
    def viewport(self) -> tuple[int, int, int, int]:
        """The Window viewport

        The Window viewport, expressed as (x, y, width, height).

        :return: The viewport size as a tuple of four ints.
        """
        return self._viewport

    @viewport.setter
    def viewport(self, values: tuple[int, int, int, int]) -> None:
        self._viewport = values
        pr = 1.0
        x, y, w, h = values
        pyglet.gl.glViewport(int(x * pr), int(y * pr), int(w * pr), int(h * pr))

    @property
    def projection(self) -> pyglet.math.Mat4:
        return self._projection_matrix

    @projection.setter
    def projection(self, matrix: pyglet.math.Mat4) -> None:
        with self.ubo as window_block:
            window_block.projection[:] = matrix

        self._projection_matrix = matrix

    @property
    def view(self) -> pyglet.math.Mat4:
        """The OpenGL window view matrix. Read-write.

        The default view is an identity matrix, but a custom
        :py:class:`pyglet.math.Mat4` instance can be set.
        Alternatively, you can supply a flat tuple of 16 values.
        """
        return self._view_matrix

    @view.setter
    def view(self, matrix: pyglet.math.Mat4) -> None:

        with self.ubo as window_block:
            window_block.view[:] = matrix

        self._view_matrix = matrix


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
    sys.exit(app.exec_())
