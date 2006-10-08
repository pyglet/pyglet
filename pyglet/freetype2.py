
from ctypes import *
from ctypes import util

from pyglet.image import Image

path = util.find_library('freetype')
_libfreetype = cdll.LoadLibrary(path)

def _get_function(name, argtypes, rtype):
    try:
        func = getattr(_libfreetype, name)
        func.argtypes = argtypes
        func.restype = rtype
        return func
    except AttributeError, e:
            raise ImportError(e)

FT_Done_FreeType = _get_function('FT_Done_FreeType', [c_void_p], None)
FT_Done_Face = _get_function('FT_Done_Face', [c_void_p], None)

class Error(Exception): pass

class FT_LibraryRec(Structure):
    _fields_ = [
        ('dummy', c_int),
    ]

    def __del__(self, byref=byref, FT_Done_FreeType=FT_Done_FreeType):
        global _library
        FT_Done_FreeType(byref(self))
        _library = None
FT_Library = POINTER(FT_LibraryRec)

class FT_Glyph_Metrics(Structure):
    _fields_ = [
        ('width', c_long),
        ('height', c_long),
        ('horiBearingX', c_long),
        ('horiBearingY', c_long),
        ('horiAdvance', c_long),
        ('vertBearingX', c_long),
        ('vertBearingY', c_long),
        ('vertAdvance', c_long),
    ]

class FT_Generic(Structure):
    _fields_ = [('data', c_void_p), ('finalizer', c_void_p)]

class FT_BBox(Structure):
    _fields_ = [('xMin', c_long), ('yMin', c_long), ('xMax', c_long),
        ('yMax', c_long)]

class FT_Vector(Structure):
    _fields_ = [('x', c_long), ('y', c_long)]

class FT_Bitmap(Structure):
    _fields_ = [
        ('rows', c_int),
        ('width', c_int),
        ('pitch', c_int),
        # declaring buffer as c_char_p confuses ctypes, poor dear
        ('buffer', POINTER(c_ubyte)),
        ('num_grays', c_short),
        ('pixel_mode', c_char),
        ('palette_mode', c_char),
        ('palette', c_void_p),
    ]

class FT_Outline(Structure):
    _fields_ = [
        ('n_contours', c_short),      # number of contours in glyph
        ('n_points', c_short),        # number of points in the glyph
        ('points', POINTER(FT_Vector)),  # the outline's points
        ('tags', c_char_p),            # the points flags
        ('contours', POINTER(c_short)),  # the contour end points
        ('flags', c_int),             # outline masks
    ]

class FT_GlyphSlotRec(Structure):
    _fields_ = [
        ('library', FT_Library),
        ('face', c_void_p),
        ('next', c_void_p),
        ('reserved', c_uint),
        ('generic', FT_Generic),

        ('metrics', FT_Glyph_Metrics),
        ('linearHoriAdvance', c_long),
        ('linearVertAdvance', c_long),
        ('advance', FT_Vector),

        ('format', c_int),

        ('bitmap', FT_Bitmap),
        ('bitmap_left', c_int),
        ('bitmap_top', c_int),

        ('outline', FT_Outline),
        ('num_subglyphs', c_uint),
        ('subglyphs', c_void_p),

        ('control_data', c_void_p),
        ('control_len', c_long),

        ('lsb_delta', c_long),
        ('rsb_delta', c_long),
        ('other', c_void_p),
        ('internal', c_void_p),
    ]
FT_GlyphSlot = POINTER(FT_GlyphSlotRec)

class FT_Size_Metrics(Structure):
    _fields_ = [
        ('x_ppem', c_ushort),    # horizontal pixels per EM
        ('y_ppem', c_ushort),    # vertical pixels per EM

        ('x_scale', c_long),     # two scales used to convert font units
        ('y_scale', c_long),     # to 26.6 frac. pixel coordinates

        ('ascender', c_long),    # ascender in 26.6 frac. pixels
        ('descender', c_long),   # descender in 26.6 frac. pixels
        ('height', c_long),      # text height in 26.6 frac. pixels
        ('max_advance', c_long), # max horizontal advance, in 26.6 pixels
    ]

class FT_SizeRec(Structure):
    _fields_ = [
        ('face', c_void_p),
        ('generic', c_void_p),
        ('metrics', FT_Size_Metrics),
        ('internal', c_void_p),
    ]
FT_Size = POINTER(FT_SizeRec)

class FT_FaceRec(Structure):
    _fields_ = [
          ('num_faces', c_long),
          ('face_index', c_long),

          ('face_flags', c_long),
          ('style_flags', c_long),

          ('num_glyphs', c_long),
          ('family_name', c_char_p),
          ('style_name', c_char_p),

          ('num_fixed_sizes', c_int),
          ('available_sizes', c_void_p),

          ('num_charmaps', c_int),
          ('charmaps', c_void_p),

          ('generic', FT_Generic),

          ('bbox', FT_BBox),

          ('units_per_EM', c_ushort),
          ('ascender', c_short),
          ('descender', c_short),
          ('height', c_short),

          ('max_advance_width', c_short),
          ('max_advance_height', c_short),

          ('underline_position', c_short),
          ('underline_thickness', c_short),

          ('glyph', FT_GlyphSlot),
          ('size', FT_Size),
          ('charmap', c_void_p),

          ('driver', c_void_p),
          ('memory', c_void_p),
          ('stream', c_void_p),

          ('sizes_list_head', c_void_p),
          ('sizes_list_tail', c_void_p),

          ('autohint', FT_Generic),
          ('extensions', c_void_p),
          ('internal', c_void_p),
    ]

    def __del__(self, byref=byref, FT_Done_Face=FT_Done_Face):
        # FT_Done_FreeType doc says it will free up faces...
        if _library is not None:
            FT_Done_Face(byref(self))

FT_Face = POINTER(FT_FaceRec)

FT_LOAD_RENDER = 0x4

FT_Init_FreeType = _get_function('FT_Init_FreeType',
    [POINTER(FT_Library)], c_int)
FT_New_Memory_Face = _get_function('FT_New_Memory_Face',
    [FT_Library, c_char_p, c_long, c_long, POINTER(FT_Face)], c_int)
FT_Set_Pixel_Sizes = _get_function('FT_Set_Pixel_Sizes',
    [FT_Face, c_uint, c_uint], c_int)
FT_Load_Glyph = _get_function('FT_Load_Glyph',
    [FT_Face, c_uint, c_int32], c_int)
FT_Load_Char = _get_function('FT_Load_Char',
    [FT_Face, c_ulong, c_int], c_int)

_library = None

def load_face(path, height):
    global _library
    if _library is None:
        # init the library
        _library = FT_Library()
        error = FT_Init_FreeType(byref(_library))
        if error:
            raise Error('an error occurred during library initialization')

    # have Python open and read the file as it handles errors nicely
    fp = open(path, 'rb')
    font_data = fp.read()
    fp.close()

    face = FT_Face()
    error = FT_New_Memory_Face(_library, font_data, len(font_data),
        0, byref(face));
    if error:
        print error
        raise Error('an error occurred during face loading')

    # "height" pixels high
    error = FT_Set_Pixel_Sizes(face, 0, height)
    if error:
        raise Error("couldn't get requested height")

    return face
    
def render_char(face, c):
    if FT_Load_Char(face, c_ulong(ord(c)), FT_LOAD_RENDER):
        raise Error('an error occurred drawing the glyph %r'%c)

    f = face.contents
    g = f.glyph.contents
    b = g.bitmap

    # expand single grey channel out to RGBA
    s = []
    for i in range(b.rows):
        for j in range(b.width):
            elem = chr(b.buffer[i*b.width + j])
            s.append(elem)
            s.append(elem)
            s.append(elem)
            s.append(elem)

    return Image(''.join(s), b.width, b.rows, 4)

if __name__ == '__main__':
    f = load_face("/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf", 16)
    render_char(f, 'A')
    FT_Load_Glyph(f, 0, FT_LOAD_RENDER)
    f = f.contents
    print '='*75
    print 'f =', f
    for name, type in f._fields_:
        print 'FACE', name, getattr(f, name)

    print '-'*75
    g = f.glyph.contents
    print 'g =', g
    for name, type in g._fields_:
        print 'GLYPH', name, getattr(g, name)

    b = g.bitmap
    print '-'*75
    print 'b =', b
    for name, type in b._fields_:
        print 'BITMAP', name, type, getattr(b, name)

