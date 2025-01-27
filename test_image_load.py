import pyglet
import time

t = time.perf_counter()
img = pyglet.image.load("4096.png")
print("Loaded:", time.perf_counter() - t, "Format:", img.format)

#t1 = time.perf_counter()
#converted = img.get_image_data().get_data('RGBA')
#print("Regex convert image time:", time.perf_counter() - t1)