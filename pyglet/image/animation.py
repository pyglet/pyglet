"""2D Animations.

Animations can be used by the :py:class:`~pyglet.sprite.Sprite` class in place
of static images. They are essentially containers for individual image frames,
with a duration per frame. They can be infinitely looping, or stop at the last
frame. You can load Animations from disk, such as from GIF files::

    ani = pyglet.resource.animation('walking.gif')
    sprite = pyglet.sprite.Sprite(img=ani)

Alternatively, you can create your own Animations from a sequence of images
by using the :py:meth:`~Animation.from_image_sequence` method::

    images = [pyglet.resource.image('walk_a.png'),
              pyglet.resource.image('walk_b.png'),
              pyglet.resource.image('walk_c.png')]

    ani = pyglet.image.Animation.from_image_sequence(images, duration=0.1, loop=True)

You can also use an :py:class:`pyglet.image.ImageGrid`, which is iterable::

    sprite_sheet = pyglet.resource.image('my_sprite_sheet.png')
    image_grid = pyglet.image.ImageGrid(sprite_sheet, rows=1, columns=5)

    ani = pyglet.image.Animation.from_image_sequence(image_grid, duration=0.1)

In the above examples, all the Animation Frames have the same duration.
If you wish to adjust this, you can manually create the Animation from a list of
:py:class:`~AnimationFrame`::

    image_a = pyglet.resource.image('walk_a.png')
    image_b = pyglet.resource.image('walk_b.png')
    image_c = pyglet.resource.image('walk_c.png')

    frame_a = pyglet.image.AnimationFrame(image_a, duration=0.1)
    frame_b = pyglet.image.AnimationFrame(image_b, duration=0.2)
    frame_c = pyglet.image.AnimationFrame(image_c, duration=0.1)

    ani = pyglet.image.Animation(frames=[frame_a, frame_b, frame_c])

"""
from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal
    from pyglet.image import AbstractImage, AbstractImageSequence
    from pyglet.image.atlas import TextureBin


class Animation:
    """Sequence of images with timing information.

    Animations are a collection of :py:class:`~AnimationFrame`s, which are
    simple containers for Image data and duration information.

    If no frames of the animation have a duration of ``None``, the animation
    loops continuously; otherwise the animation stops at the first frame with
    duration of ``None``.
    """

    def __init__(self, frames: list[AnimationFrame]) -> None:
        """Create an animation directly from a list of frames."""
        assert len(frames)
        self.frames = frames

    def add_to_texture_bin(self, texture_bin: TextureBin, border: int = 0) -> None:
        """Add the images of the animation to a :py:class:`~pyglet.image.atlas.TextureBin`.

        The animation frames are modified in-place to refer to the texture bin
        regions. An optional border (in pixels) can be specified to reserve around
        the images that are added to the texture bin.
        """
        for frame in self.frames:
            frame.image = texture_bin.add(frame.image, border)

    def get_transform(self, flip_x: bool = False, flip_y: bool = False,
                      rotate: Literal[0, 90, 180, 270, 360] = 0) -> Animation:
        """Create a copy of this animation, applying a simple transformation.

        The transformation is performed by manipulating the texture coordinates,
        which limits this operation to increments of 90 degrees.

        The transformation is applied around the image's anchor point of
        each frame.  The texture data is shared between the original animation
        and the transformed animation.
        """
        frames = [AnimationFrame(frame.image.get_texture().get_transform(flip_x, flip_y, rotate),
                                 frame.duration) for frame in self.frames]
        return Animation(frames)

    def get_duration(self) -> float:
        """Get the total duration of the animation in seconds."""
        return sum([frame.duration for frame in self.frames if frame.duration is not None])

    def get_max_width(self) -> int:
        """Get the maximum image frame width.

        This method is useful for determining texture space requirements: due
        to the use of ``anchor_x`` the actual required viewing area during
         playback may be larger.
        """
        return max([frame.image.width for frame in self.frames])

    def get_max_height(self) -> int:
        """Get the maximum image frame height.

        This method is useful for determining texture space requirements: due
        to the use of ``anchor_y`` the actual required viewing area during
        playback may be larger.
        """
        return max([frame.image.height for frame in self.frames])

    @classmethod
    def from_image_sequence(cls, sequence: AbstractImageSequence, duration: float, loop: bool = True) -> Animation:
        """Create an animation from a list of images and a per-frame duration."""
        frames = [AnimationFrame(image, duration) for image in sequence]
        if not loop:
            frames[-1].duration = None
        return cls(frames)

    def __repr__(self) -> str:
        return f"Animation(frames={len(self.frames)})"


class AnimationFrame:
    """A single frame of an animation."""

    __slots__ = 'image', 'duration'

    def __init__(self, image: AbstractImage, duration: float | None) -> None:
        """Create an animation frame from an image."""
        self.image = image
        self.duration = duration

    def __repr__(self) -> str:
        return f"AnimationFrame({self.image}, duration={self.duration})"
