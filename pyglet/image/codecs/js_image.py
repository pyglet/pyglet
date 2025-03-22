import asyncio

from pyglet.image import ImageDecoder
from pyglet.image import ImageData
from pyglet.image.codecs import ImageDecodeException

try:
    import js
    import pyodide.ffi
except ImportError:
    raise ImportError


_image_canvas = js.document.createElement("canvas")
_image_context = _image_canvas.getContext("2d", willReadFrequently=True)

async def check_image_exists(url):
    """Check if an image exists at the given URL."""
    try:
        response = await js.fetch(url, {"method": "HEAD"})  # HEAD request (faster than GET)
        if response.ok:
            print(f"Image exists: {url}")
            return True
        else:
            print(f"Image does NOT exist: {url} (Status: {response.status})")
            return False
    except Exception as e:
        print(f"Error checking image: {e}")
        return False

class JSImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['.png']

    async def decode(self, filename, file) -> ImageData:
        img = js.Image.new()
        img.src = filename

        await pyodide.ffi.to_js(img.decode())  # Wait for image to load

        _image_canvas.width = img.width
        _image_canvas.height = img.height

        # Clear previous image
        _image_context.clearRect(0, 0, img.width, img.height)

        # Draw to context
        _image_context.translate(0, img.height)  # Move down
        _image_context.scale(1, -1)  # Flip vertically
        _image_context.drawImage(img, 0, 0)

        image_data = _image_context.getImageData(0, 0, img.width, img.height)
        pixel_data = image_data.data  # Uint8Array

        return ImageData(img.width, img.height, 'RGBA', pixel_data)

    def decode_animation(self, filename, file):
        """Decode the given file object and return an instance of :py:class:`~pyglet.image.Animation`.
        Throws ImageDecodeException if there is an error.  filename
        can be a file type hint.
        """
        raise ImageDecodeException('This decoder cannot decode animations.')

    def __repr__(self) -> str:
        return "{}{}".format(self.__class__.__name__,
                               self.get_animation_file_extensions() +
                               self.get_file_extensions())
def get_decoders():
    return [JSImageDecoder()]

def get_encoders():
    return []