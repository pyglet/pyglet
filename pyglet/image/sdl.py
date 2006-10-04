from ctypes import *
import os.path

from SDL import *

try:
    from SDL.image import *
    _have_SDL_image = True
except:
    _have_SDL_image = False

def load(file):
    '''Load an SDL_Surface from a file object or filename.'''
    if not hasattr(file, 'read'):
        file = open(file, 'rb')

    image = None
    if _have_SDL_image:
        try:
            image = IMG_Load_RW(SDL_RWFromObject(file), 0)
        except:
            pass

    if not image:
        try:
            image = SDL_LoadBMP_RW(SDL_RWFromObject(file), 0)
        except:
            pass

    if not image:
        raise IOError('Could not open file using any available image loader.')

    return image

def create_surface(texture, level=0):
    surface = SDL_CreateRGBSurface(SDL_SWSURFACE, 
                                   texture.size[0], texture.size[1], 32,
                                   SDL_SwapLE32(0x000000ff),
                                   SDL_SwapLE32(0x0000ff00),
                                   SDL_SwapLE32(0x00ff0000),
                                   SDL_SwapLE32(0xff000000))
    SDL_LockSurface(surface)

    glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
    glPixelStorei(GL_PACK_ROW_LENGTH, 
                  surface.pitch / surface.format.BytesPerPixel)
    glBindTexture(GL_TEXTURE_2D, texture.id)
    glGetTexImage(GL_TEXTURE_2D, level, GL_RGBA, GL_UNSIGNED_BYTE,
                  surface.pixels.as_ctypes())
    glPopClientAttrib()

    SDL_UnlockSurface(surface)
    return surface

def save(image, file, format=None):
    '''Save a texture or SDL_Surface to a file object or filename.'''
    if isinstance(image, Texture):
        image = create_surface(image)

    if not hasattr(file, 'write'):
        format = os.path.splitext(file)[1]
        file = open(file, 'wb')

    if format == '.bmp':
        SDL_SaveBMP_RW(image, SDL_RWFromObject(file), 1)
    else:
        raise IOError('Could not save file')

