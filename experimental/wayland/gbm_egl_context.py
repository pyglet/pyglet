# from ctypes import *
#
# from . import xkbcommon
#
#
# ctx = xkbcommon.xkb_context_new(xkbcommon.XKB_CONTEXT_NO_FLAGS)
# print(ctx)
#
# # TODO: get a real string from Wayland:
# keymap_string = create_string_buffer(b"ACTUAL KEYMAP STRING HERE")
#
# keymap = xkbcommon.xkb_keymap_new_from_string(ctx, keymap_string, xkbcommon.XKB_KEYMAP_FORMAT_TEXT_V1,
#                                               xkbcommon.XKB_KEYMAP_COMPILE_NO_FLAGS)
# print(keymap)
#
# state = xkbcommon.xkb_state_new(keymap)

import os

from pyglet.libs.wayland.gbm import *
from pyglet.libs.egl.egl import *
from pyglet.libs.egl.eglext import *

assert eglBindAPI(EGL_OPENGL_API) == EGL_TRUE

try:
    cards = [f for f in os.listdir('/dev/dri/') if f.startswith('card')]
    cards = [os.path.join('/dev/dri/', name) for name in cards]
    assert cards
except (OSError, AssertionError):
    print("unable to find DRI device")
    exit()

# Open the first GBM device, and create a surface
fd = os.open(cards[0], os.O_RDWR | os.MFD_CLOEXEC)
gbm_device = gbm_create_device(fd)
gbm_surface = gbm_surface_create(gbm_device, 256, 256, GBM_FORMAT_XRGB8888, GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING)


# Get a native GBM platform display
dpy = eglGetPlatformDisplay(EGL_PLATFORM_GBM_MESA, gbm_device, None)
print("Display: ", dpy)
# Initialize EGL:
major, minor = EGLint(), EGLint()
result = eglInitialize(dpy, major, minor)
assert result == 1, "EGL Initialization Failed"
print("Initialized EGL: ", major.value, minor.value)

# Get the number of configs:
num_configs = EGLint()
result = eglGetConfigs(dpy, None, 0, num_configs)
assert result == EGL_TRUE, "Failed to query Configs"
print("Number of configs available: ", num_configs.value)

configs = (EGLConfig * num_configs.value)()
result = eglGetConfigs(dpy, configs, num_configs, byref(num_configs))
assert result == EGL_TRUE, "Failed to query Configs"

for config in configs:
    # For a test, just go with the first successful Config
    srf = eglCreatePlatformWindowSurface(dpy, config, gbm_surface, None)
    if srf:
        print("Surface: ", srf)
        break
else:
    print("No Surface Found")
    exit()


ctx = eglCreateContext(dpy, config, None, None)
print("Context:", ctx)

assert eglMakeCurrent(dpy, srf, srf, ctx) == EGL_TRUE, "Failed to Make Context Current"

eglDestroySurface(dpy, srf)
eglDestroyContext(dpy, ctx)
eglTerminate(dpy)

gbm_device_destroy(gbm_device)
os.close(fd)
