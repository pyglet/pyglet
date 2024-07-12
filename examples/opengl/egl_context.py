from pyglet.libs.egl import egl as libegl
from pyglet.libs.egl.egl import (
    EGL_SINGLE_BUFFER, EGL_BACK_BUFFER, EGL_NONE, EGL_OPENGL_API, EGL_OPENGL_ES_API,
    EGL_SUCCESS, EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_BLUE_SIZE, EGL_GREEN_SIZE, EGL_RED_SIZE,
    EGL_DEPTH_SIZE, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT, EGL_NONE, EGL_WIDTH, EGL_HEIGHT,
    EGL_CONTEXT_MAJOR_VERSION, EGL_RENDER_BUFFER,
)


_buffer_types = {EGL_SINGLE_BUFFER: "EGL_RENDER_BUFFER",
                 EGL_BACK_BUFFER: "EGL_BACK_BUFFER",
                 EGL_NONE: "EGL_NONE"}

_api_types = {EGL_OPENGL_API: "EGL_OPENGL_API",
              EGL_OPENGL_ES_API: "EGL_OPENGL_ES_API",
              EGL_NONE: "EGL_NONE"}

# Initialize a display:
display = libegl.EGLNativeDisplayType()
display_connection = libegl.eglGetDisplay(display)

majorver = libegl.EGLint()
minorver = libegl.EGLint()
result = libegl.eglInitialize(display_connection, majorver, minorver)
assert result == 1, "EGL Initialization Failed"
egl_version = majorver.value, minorver.value
print(f"EGL version: {egl_version}")

# Get the number of configs:
num_configs = libegl.EGLint()
config_size = libegl.EGLint()
result = libegl.eglGetConfigs(display_connection, None, config_size, num_configs)
assert result == 1, "Failed to query Configs"

print("Number of configs available: ", num_configs.value)

# Choose a config:
config_attribs = (EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
                  EGL_BLUE_SIZE, 8,
                  EGL_GREEN_SIZE, 8,
                  EGL_RED_SIZE, 8,
                  EGL_DEPTH_SIZE, 8,
                  EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
                  EGL_NONE)
config_attrib_array = (libegl.EGLint * len(config_attribs))(*config_attribs)
egl_config = libegl.EGLConfig()
result = libegl.eglChooseConfig(display_connection, config_attrib_array, egl_config, 1, num_configs)
assert result == 1, "Failed to choose Config"

# Create a surface:
pbufferwidth = 1
pbufferheight = 1
pbuffer_attribs = (EGL_WIDTH, pbufferwidth, EGL_HEIGHT, pbufferheight, EGL_NONE)
pbuffer_attrib_array = (libegl.EGLint * len(pbuffer_attribs))(*pbuffer_attribs)
surface = libegl.eglCreatePbufferSurface(display_connection, egl_config, pbuffer_attrib_array)
print("Surface id: ", surface)

# Bind the API:
result = libegl.eglBindAPI(libegl.EGL_OPENGL_API)
assert result == 1, "Failed to bind EGL_OPENGL_API"

# Create a context:
context_attribs = (EGL_CONTEXT_MAJOR_VERSION, 2, EGL_NONE)
context_attrib_array = (libegl.EGLint * len(context_attribs))(*context_attribs)
context = libegl.eglCreateContext(display_connection, egl_config, None, context_attrib_array)
print("Context id: ", context)

# Make context current:
result = libegl.eglMakeCurrent(display_connection, surface, surface, context)
assert result == 1, "Failed to make context current"

error_code = libegl.eglGetError()
assert error_code == EGL_SUCCESS, f"EGL Error code {error_code} returned"

# Print some context details:
buffer_type = libegl.EGLint()
libegl.eglQueryContext(display_connection, context, EGL_RENDER_BUFFER, buffer_type)
print("Buffer type: ", _buffer_types.get(buffer_type.value, "Unknown"))
print("API type: ", _api_types.get(libegl.eglQueryAPI(), "Unknown"))

# Terminate EGL:
libegl.eglTerminate(display_connection)
