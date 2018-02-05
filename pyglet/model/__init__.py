from pyglet.model import codecs as _codecs
from pyglet.compat import BytesIO
from pyglet.gl import *
from pyglet import graphics


class ModelException(Exception):
    pass


def load(filename, file=None, decoder=None, batch=None):
    """Load a 3D model from a file.

    :Parameters:
        `filename` : str
            Used to guess the model format, and to load the file if `file` is
            unspecified.
        `file` : file-like object or None
            Source of model data in any supported format.        
        `decoder` : ModelDecoder or None
            If unspecified, all decoders that are registered for the filename
            extension are tried.  If none succeed, the exception from the
            first decoder is raised.
        `batch` : Batch or None
            An optional Batch instance to add this model to. 

    :rtype: Model
    """

    if not file:
        file = open(filename, 'rb')

    if not hasattr(file, 'seek'):
        file = BytesIO(file.read())

    try:
        if decoder:
            return decoder.decode(file, filename, batch)
        else:
            first_exception = None
            for decoder in _codecs.get_decoders(filename):
                try:
                    model = decoder.decode(file, filename, batch)
                    return model
                except _codecs.ModelDecodeException as e:
                    if (not first_exception or
                            first_exception.exception_priority < e.exception_priority):
                        first_exception = e
                    file.seek(0)

            if not first_exception:
                raise _codecs.ModelDecodeException('No decoders are available'
                                                   'for this model format.')
            raise first_exception
    finally:
        file.close()


class Model(object):

    def __init__(self, mesh_list, batch):
        self._batch = batch
        self.mesh_list = mesh_list
        self.vertex_list_map = {}
        self.texture_map = {}

        for mesh in mesh_list:
            material = mesh.material
            if material.texture_name:
                texture = pyglet.image.load(material.texture_name).get_texture()
                group = TexturedMaterialGroup(material, texture)
                self.texture_map[texture] = group
            else:
                group = MaterialGroup(material)

            vlist = batch.add(len(mesh.vertices) // 3,
                              GL_TRIANGLES,
                              group,
                              ('v3f/static', mesh.vertices),
                              ('n3f/static', mesh.normals),
                              ('t2f/static', mesh.tex_coords))

            self.vertex_list_map[vlist] = group

    @property
    def batch(self):
        """The graphics Batch that the Model belongs to.

        The Model can be migrated from one batch to another, or removed from
        a batch (for individual drawing). If not part of any batch, the Model
        will keep it's own internal batch. Note that batch migration can be
        an expensive operation.

        :type: :py:class:`pyglet.graphics.Batch`
        """
        return self._batch

    @batch.setter
    def batch(self, batch):
        if self._batch == batch:
            return

        if batch is None:
            batch = pyglet.graphics.Batch()
            for vlist, group in self.vertex_list_map.items():
                self._batch.migrate(vlist, GL_TRIANGLES, group, batch)
            self._batch = batch
        else:
            for vlist, group in self.vertex_list_map.items():
                self._batch.migrate(vlist, GL_TRIANGLES, group, batch)
            self._batch = batch

    def update(self, x=None, y=None, z=None):
        """Shift the model on the x, y or z axis."""
        if x:
            for vlist in self.vertex_list_map:
                verts = vlist.vertices[:]
                vlist.vertices[0::3] = [v + x for v in verts[0::3]]
        if y:
            for vlist in self.vertex_list_map:
                verts = vlist.vertices[:]
                vlist.vertices[1::3] = [v + y for v in verts[1::3]]
        if z:
            for vlist in self.vertex_list_map:
                verts = vlist.vertices[:]
                vlist.vertices[2::3] = [v + z for v in verts[2::3]]

    def draw(self):
        self._batch.draw_subset(self.vertex_list_map.keys())


class TexturedMaterialGroup(graphics.Group):

    def __init__(self, material, texture):
        super(TexturedMaterialGroup, self).__init__()
        self.material = material
        self.diffuse = (GLfloat * 4)(*(material.diffuse + [material.opacity]))
        self.ambient = (GLfloat * 4)(*(material.ambient + [material.opacity]))
        self.specular = (GLfloat * 4)(*(material.specular + [material.opacity]))
        self.emission = (GLfloat * 4)(*(material.emission + [material.opacity]))
        self.shininess = material.shininess
        self.texture = texture

    def set_state(self, face=GL_FRONT_AND_BACK):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
        glMaterialfv(face, GL_DIFFUSE, self.diffuse)
        glMaterialfv(face, GL_AMBIENT, self.ambient)
        glMaterialfv(face, GL_SPECULAR, self.specular)
        glMaterialfv(face, GL_EMISSION, self.emission)
        glMaterialf(face, GL_SHININESS, self.shininess)

    def unset_state(self):
        glDisable(self.texture.target)
        glDisable(GL_COLOR_MATERIAL)

    def __eq__(self, other):
        return (self.texture.id == other.texture.id and
                self.texture.target == other.texture.target and
                self.diffuse[:] == other.diffuse[:] and
                self.ambient[:] == other.ambient[:] and
                self.specular[:] == other.specular[:] and
                self.emission[:] == other.emission[:] and
                self.shininess == other.shininess)

    def __hash__(self):
        return hash((self.texture.id, self.texture.target))


class MaterialGroup(graphics.Group):

    def __init__(self, material):
        super(MaterialGroup, self).__init__()
        self.material = material
        self.diffuse = (GLfloat * 4)(*(material.diffuse + [material.opacity]))
        self.ambient = (GLfloat * 4)(*(material.ambient + [material.opacity]))
        self.specular = (GLfloat * 4)(*(material.specular + [material.opacity]))
        self.emission = (GLfloat * 4)(*(material.emission + [material.opacity]))
        self.shininess = material.shininess

    def set_state(self, face=GL_FRONT_AND_BACK):
        glDisable(GL_TEXTURE_2D)
        glMaterialfv(face, GL_DIFFUSE, self.diffuse)
        glMaterialfv(face, GL_AMBIENT, self.ambient)
        glMaterialfv(face, GL_SPECULAR, self.specular)
        glMaterialfv(face, GL_EMISSION, self.emission)
        glMaterialf(face, GL_SHININESS, self.shininess)

    def unset_state(self):
        glDisable(GL_COLOR_MATERIAL)

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.diffuse[:] == other.diffuse[:] and
                self.ambient[:] == other.ambient[:] and
                self.specular[:] == other.specular[:] and
                self.emission[:] == other.emission[:] and
                self.shininess == other.shininess)

    def __hash__(self):
        return hash((tuple(self.diffuse) + tuple(self.ambient) +
                     tuple(self.specular) + tuple(self.emission), self.shininess))


_codecs.add_default_model_codecs()
