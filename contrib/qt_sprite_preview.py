"""Requires: PyQT5
   An example using PyQT5 and Pyglet together.
   This is a sprite previewer, you can edit the fragment and vertex shaders and compile it to get a live view.
   Errors and success will be printed in console.

   To load images, choose File -> Open Image.
   Images loaded will be listed in the Images menu.
   By unchecking an image (or clicking on it), it will be deleted from the list.

   Names in parentheses will be used for the sampler2D name.
"""

import os
import sys
import pyglet

from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QOpenGLWidget
from pyglet.gl import glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glActiveTexture, GL_TEXTURE0, glBindTexture, \
    GL_BLEND, glEnable, glBlendFunc, glDisable

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
    """A sprite group that uses multiple active textures.
    """

    def __init__(self, textures, blend_src, blend_dest, program=None, order=0, parent=None):
        """Create a sprite group for multiple textures and samplers.
           All textures must share the same target type.

        :Parameters:
            `textures` : `dict`
                Textures in samplername : texture.
            `blend_src` : int
                OpenGL blend source mode; for example,
                ``GL_SRC_ALPHA``.
            `blend_dest` : int
                OpenGL blend destination mode; for example,
                ``GL_ONE_MINUS_SRC_ALPHA``.
            `parent` : `~pyglet.graphics.Group`
                Optional parent group.
        """
        self.images = textures
        texture = list(self.images.values())[0]
        self.target = texture.target
        super().__init__(texture, blend_src, blend_dest, program, order, parent)

        self.program.use()
        for idx, name in enumerate(self.images):
            try:
                self.program[name] = idx
            except Exception:
                print(f"Uniform: {name} not found.")

        self.program.stop()

    def set_state(self):
        self.program.use()

        for i, texture in enumerate(self.images.values()):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(self.target, texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()
        glActiveTexture(GL_TEXTURE0)

    def __repr__(self):
        return '%s(%r-%d)' % (self.__class__.__name__, self.texture, self.texture.id)

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.images == other.textures and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((id(self.parent),
                     id(self.images),
                     self.blend_src, self.blend_dest))


class MultiTextureSprite(pyglet.sprite.AdvancedSprite):

    def __init__(self,
                 imgs, x=0, y=0, z=0,
                 blend_src=pyglet.gl.GL_SRC_ALPHA,
                 blend_dest=pyglet.gl.GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 subpixel=False,
                 program=None):

        self._x = x
        self._y = y
        self._z = z

        self._texture = list(imgs.values())[0]

        if isinstance(self._texture, pyglet.image.TextureArrayRegion):
            self._program = program or pyglet.sprite.get_default_array_shader()
        else:
            self._program = program or pyglet.sprite.get_default_shader()

        self._batch = batch or pyglet.graphics.get_default_batch()

        self._group = MultiTextureSpriteGroup(imgs, blend_src, blend_dest, self.program, 0, group)

        self._subpixel = subpixel
        self._create_vertex_list()


class Ui_MainWindow:
    SPRITE_POSITION = (0, 0)

    def __init__(self):
        self.images = []

        self.group = pyglet.graphics.Group()

        self.sprite = None
        self.program = None

    def setupUi(self, MainWindow):
        self._window = MainWindow

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(820, 855)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
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
        self.openGLWidget = PygletWidget(800, 400, self.centralwidget, self)
        self.openGLWidget.setMinimumSize(QtCore.QSize(800, 400))
        self.openGLWidget.setObjectName("openGLWidget")
        self.verticalLayout_3.addWidget(self.openGLWidget)
        self.gridLayout.addLayout(self.verticalLayout_3, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 820, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.actionOpen_Image = QtWidgets.QAction(MainWindow)
        self.actionOpen_Image.setObjectName("actionOpen_Image")
        self.actionOpen_Image.triggered.connect(self.loadImages)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.triggered.connect(self.closeProgram)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionOpen_Image)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.imageMenu = QtWidgets.QMenu(self.menubar)
        self.imageMenu.setObjectName("imageMenu")
        self.noImageAction = QtWidgets.QAction(MainWindow)
        self.noImageAction.setDisabled(True)
        self.imageMenu.addAction(self.noImageAction)

        self.menubar.addAction(self.imageMenu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def compileClick(self):
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
                self.sprite = pyglet.sprite.AdvancedSprite(self.images[0], x=self.SPRITE_POSITION[0],
                                                           y=self.SPRITE_POSITION[1], group=self.group,
                                                           batch=self.openGLWidget.batch, program=self.program)
            else:
                textures = {image.shader_name: image.get_texture() for image in self.images}
                self.sprite = MultiTextureSprite(textures, x=self.SPRITE_POSITION[0], y=self.SPRITE_POSITION[1],
                                                 group=self.group, batch=self.openGLWidget.batch, program=self.program)

            if self.program:
                print("Successfully compiled shader.")
        except pyglet.gl.lib.GLException as err:
            print(f"Failed to compile shader: {err}")
        except Exception as err:
            print("Unexpected error", err)

    def loadImages(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self._window, "Select Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp)",
                                                  options=options)
        if fileName:
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

    def removeImage(self, actionWidget):
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

    def closeProgram(self):
        app.exit()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Sprite Shader Previewer"))
        self.label.setText(_translate("MainWindow", "Vertex Source:"))
        self.label_2.setText(_translate("MainWindow", "Fragment Source:"))
        self.compileShaderBtn.setText(_translate("MainWindow", "Compile Shaders"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen_Image.setText(_translate("MainWindow", "Open Image"))
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

    def __init__(self, width, height, parent, mainWindow):
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setMinimumSize(width, height)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._pyglet_update)
        self.timer.setInterval(0)
        self.timer.start()

        self.elapsed = 0

        pyglet.clock.schedule_interval(self.update_time_uniform, 1 / 60.0)

    def update_time_uniform(self, dt):
        self.elapsed += dt

        if self.mainWindow.program:
            self.mainWindow.program.use()

            # Ignore time if it doesn't exist.
            try:
                self.mainWindow.program['time'] = self.elapsed
            except Exception:
                pass

            self.mainWindow.program.stop()

    def _pyglet_update(self):
        # Tick the pyglet clock, so scheduled events can work.
        pyglet.clock.tick()

        # Force widget to update, otherwise paintGL will not be called.
        self.update()  # self.updateGL() for pyqt5

    def paintGL(self):
        """Pyglet equivalent of on_draw event for window"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.batch.draw()

    def resizeGL(self, width, height):
        self.projection = pyglet.math.Mat4.orthogonal_projection(0, width, 0, height, -255, 255)

        self.viewport = 0, 0, width, height

    def initializeGL(self):
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
    def viewport(self):
        """The Window viewport

        The Window viewport, expressed as (x, y, width, height).

        :rtype: (int, int, int, int)
        :return: The viewport size as a tuple of four ints.
        """
        return self._viewport

    @viewport.setter
    def viewport(self, values):
        self._viewport = values
        pr = 1.0
        x, y, w, h = values
        pyglet.gl.glViewport(int(x * pr), int(y * pr), int(w * pr), int(h * pr))

    @property
    def projection(self):
        return self._projection_matrix

    @projection.setter
    def projection(self, matrix: pyglet.math.Mat4):
        with self.ubo as window_block:
            window_block.projection[:] = matrix

        self._projection_matrix = matrix

    @property
    def view(self):
        """The OpenGL window view matrix. Read-write.

        The default view is an identity matrix, but a custom
        :py:class:`pyglet.math.Mat4` instance can be set.
        Alternatively, you can supply a flat tuple of 16 values.

        :type: :py:class:`pyglet.math.Mat4`
        """
        return self._view_matrix

    @view.setter
    def view(self, matrix: pyglet.math.Mat4):

        with self.ubo as window_block:
            window_block.view[:] = matrix

        self._view_matrix = matrix


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = Ui_MainWindow()
    window = QtWidgets.QMainWindow()
    ui.setupUi(window)
    window.show()
    sys.exit(app.exec_())
