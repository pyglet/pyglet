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

    def __init__(self, vertex_list_map, batch, own_batch):
        self._batch = batch
        self._own_batch = own_batch
        self.vertex_list_map = vertex_list_map

    @property
    def batch(self):
        """The graphics Batch the model belongs to.

        The Model can be migrated from one batch to another, or removed from
        a batch (for individual drawing).  Note that this can be an expensive
        operation.

        :type: :py:class:`pyglet.graphics.Batch`
        """
        return self._batch

    @batch.setter
    def batch(self, batch):
        if self._batch == batch:
            return

        if batch is None and not self._own_batch:
            batch = pyglet.graphics.Batch()
            for vlist, group in self.vertex_list_map.items():
                self._batch.migrate(vlist, GL_TRIANGLES, group, batch)
            self._batch = batch
            self._own_batch = True
        elif batch is not None:
            for vlist, group in self.vertex_list_map.items():
                self._batch.migrate(vlist, GL_TRIANGLES, group, batch)
            self._batch = batch
            self._own_batch = False

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
        print(self.batch)
        self._batch.draw_subset(self.vertex_list_map.keys())


class TexturedMaterialGroup(graphics.Group):

    def __init__(self, name, diffuse, ambient, specular, emission, shininess, opacity, texture):
        super(TexturedMaterialGroup, self).__init__()
        self.name = name
        self._diffuse = (GLfloat * 4)(*(diffuse + [opacity]))
        self._ambient = (GLfloat * 4)(*(ambient + [opacity]))
        self._specular = (GLfloat * 4)(*(specular + [opacity]))
        self._emission = (GLfloat * 4)(*(emission + [opacity]))
        self._shininess = shininess
        self.texture = texture

    def set_state(self, face=GL_FRONT_AND_BACK):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
        glMaterialfv(face, GL_DIFFUSE, self._diffuse)
        glMaterialfv(face, GL_AMBIENT, self._ambient)
        glMaterialfv(face, GL_SPECULAR, self._specular)
        glMaterialfv(face, GL_EMISSION, self._emission)
        glMaterialf(face, GL_SHININESS, self._shininess)

    def unset_state(self):
        glDisable(self.texture.target)
        glDisable(GL_COLOR_MATERIAL)

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.texture.id == other.texture.id and
                self.texture.target == other.texture.target and
                self.parent == other.parent)

    def __hash__(self):
        return hash((self.texture.id, self.texture.target))


class MaterialGroup(graphics.Group):

    def __init__(self, name, diffuse, ambient, specular, emission, shininess, opacity):
        super(MaterialGroup, self).__init__()
        self.name = name
        self._diffuse = (GLfloat * 4)(*(diffuse + [opacity]))
        self._ambient = (GLfloat * 4)(*(ambient + [opacity]))
        self._specular = (GLfloat * 4)(*(specular + [opacity]))
        self._emission = (GLfloat * 4)(*(emission + [opacity]))
        self._shininess = shininess

    def set_state(self, face=GL_FRONT_AND_BACK):
        glDisable(GL_TEXTURE_2D)
        glMaterialfv(face, GL_DIFFUSE, self._diffuse)
        glMaterialfv(face, GL_AMBIENT, self._ambient)
        glMaterialfv(face, GL_SPECULAR, self._specular)
        glMaterialfv(face, GL_EMISSION, self._emission)
        glMaterialf(face, GL_SHININESS, self._shininess)

    def unset_state(self):
        glDisable(GL_COLOR_MATERIAL)

    def __eq__(self, other):
        return super(MaterialGroup, self).__eq__(other)

    def __hash__(self):
        return super(MaterialGroup, self).__hash__()


_codecs.add_default_model_codecs()
