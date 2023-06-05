Playing Sound and Video
=======================

pyglet can play many audio and video formats. Audio is played back with
either OpenAL, XAudio2, DirectSound, or Pulseaudio, permitting hardware-accelerated
mixing and surround-sound 3D positioning. Video is played into OpenGL
textures, and so can be easily manipulated in real-time by applications
and incorporated into 3D environments.

Decoding of compressed audio and video is provided by `FFmpeg`_ v4 or v5, an
optional component available for Linux, Windows and Mac OS X. FFmpeg needs
to be installed separately.

If FFmpeg is not present, pyglet will at a minimum be able to play WAV files
only. Depending on the OS, an additional limited amount of compressed formats
may also be supported, but only WAV is guaranteed (see "Supported media types
" below). the This may be sufficient for many applications that require only a
small number of short sounds, in which case those applications need not distribute FFmpeg.

.. _FFmpeg: https://www.ffmpeg.org/download.html

.. _openal.org: https://www.openal.org/downloads

Audio drivers
-------------

pyglet can use OpenAL, XAudio2, DirectSound, or Pulseaudio to play back audio. Only one
of these drivers can be used in an application. In most cases you won't need
to concern yourself with choosing a driver, but you can manually select one if
desired. This must be done before the :py:mod:`pyglet.media` module is loaded.
The available drivers depend on your operating system:

    .. list-table::
        :header-rows: 1

        * - Windows
          - Mac OS X
          - Linux
        * - OpenAL [#openalf]_
          - OpenAL
          - OpenAL [#openalf]_
        * - DirectSound
          -
          -
        * - XAudio2
          -
          - Pulseaudio

The audio driver can be set through the ``audio`` key of the
:py:data:`pyglet.options` dictionary. For example::

    pyglet.options['audio'] = ('openal', 'pulse', 'xaudio2', 'directsound', 'silent')

This tells pyglet to try using the OpenAL driver first, and if not available
to try Pulseaudio, XAudio2 and DirectSound in that order. If all else fails,
no driver will be instantiated. The ``audio`` option can be a list of any of these
strings, giving the preference order for each driver:

    .. list-table::
        :header-rows: 1

        * - String
          - Audio driver
        * - ``openal``
          - OpenAL
        * - ``directsound``
          - DirectSound
        * - ``xaudio2``
          - XAudio2
        * - ``pulse``
          - Pulseaudio
        * - ``silent``
          - No audio output

You must set the ``audio`` option before importing :mod:`pyglet.media`.
You  can alternatively set it through an environment variable;
see :ref:`guide_environment-settings`.

The following sections describe the requirements and limitations of each audio
driver.

XAudio2
^^^^^^^^^^^
XAudio2 is only available on Windows Vista and above and is the replacement of
DirectSound. This provides hardware accelerated audio support for newer operating
systems.

Note that in some stripped down versions of Windows 10, XAudio2 may not be available
until the required DLL's are installed.

DirectSound
^^^^^^^^^^^

DirectSound is available only on Windows, and is installed by default.
pyglet uses only DirectX 7 features. On Windows Vista, DirectSound does not
support hardware audio mixing or surround sound.

OpenAL
^^^^^^

OpenAL is included with Mac OS X. Windows users can download a generic driver
from `openal.org`_, or from their sound device's manufacturer. Most Linux
distributions will have OpenAL available in the repositories for download.
For example, Arch users can ``pacman -S openal`` and Ubuntu users can ``apt install libopenal1``.

Pulse
^^^^^

Pulseaudio can also be used directly on Linux, and is installed by default
with most modern Linux distributions. Pulseaudio does not support positional
audio, and is limited to stereo. It is recommended to use OpenAL if positional
audio is required.

.. [#openalf] OpenAL is not installed by default on Windows, nor in many Linux
    distributions. It can be downloaded separately from your audio device
    manufacturer or `openal.org <https://www.openal.org/downloads>`_

Supported media types
---------------------

pyglet has included support for loading Wave (.wav) files, which are therefore
guaranteed to work on all platforms. pyglet will also use various platform libraries
and frameworks to support a limited amount of compressed audio types, without the need
for FFmpeg. While FFmpeg supports a large array of formats and codecs, it may be an
unnecessarily large dependency when only simple audio playback is needed.

These formats are supported natively under the following systems and codecs:

Windows Media Foundation
^^^^^^^^^^^^^^^^^^^^^^^^
Supported on Windows operating systems.

The following are supported on **Windows Vista and above**:

* MP3
* WMA
* ASF
* SAMI/SMI

The following are also supported on **Windows 7 and above**:

* AAC/ADTS

The following is undocumented but known to work on **Windows 10**:

* FLAC


GStreamer
^^^^^^^^^
Supported on Linux operating systems that have the GStreamer installed. Please note that the
associated Python packages for gobject & gst are also required. This varies by distribution,
but will often already be installed along with GStreamer.

* MP3
* FLAC
* OGG
* M4A


CoreAudio
^^^^^^^^^
Supported on Mac operating systems.

* AAC
* AC3
* AIF
* AU
* CAF
* MP3
* M4A
* SND
* SD2


PyOgg
^^^^^
Supported on Windows, Linux, and Mac operating systems.

PyOgg is a lightweight Python library that provides Python bindings for Opus, Vorbis,
and FLAC codecs.

If the PyOgg module is installed in your site packages, pyglet will optionally detect
and use it. Since not all operating systems can decode the same audio formats natively,
it can often be a hassle to choose an audio format that is truely cross platform with
a small footprint. This wrapper was created to help with that issue.

Supports the following formats:

* OGG
* FLAC
* OPUS

Refer to their installation guide found here: https://pyogg.readthedocs.io/en/latest/installation.html

FFmpeg
^^^^^^
FFmpeg requires an external dependency, please see installation instructions
in the next section below.

With FFmpeg, many common and less-common formats are supported. Due to the
large number of combinations of audio and video codecs, options, and container
formats, it is difficult to provide a complete yet useful list. Some of the
supported audio formats are:

* AU
* MP2
* MP3
* OGG/Vorbis
* WAV
* WMA

Some of the supported video formats are:

* AVI
* DivX
* H.263
* H.264
* MPEG
* MPEG-2
* OGG/Theora
* Xvid
* WMV
* Webm

For a complete list, see the FFmpeg sources. Otherwise, it is probably simpler
to try playing back your target file with the ``media_player.py`` example.

New versions of FFmpeg as they are released may support additional formats, or
fix errors in the current implementation.

FFmpeg installation
-------------------

You can install FFmpeg for your platform by following the instructions found
in the `FFmpeg download <https://www.ffmpeg.org/download.html>`_ page. You must
choose the shared build for the targeted OS with the architecture similar to
the Python interpreter.

Currently Pyglet supports versions 4.x and 5.x of FFmpeg.

Choose the correct architecture depending on the targeted
**Python interpreter**. If you're shipping your project with a 32 bits
interpreter, you must download the 32 bits shared binaries.

On Windows, the usual error message when the wrong architecture was downloaded
is::

    WindowsError: [Error 193] %1 is not a valid Win32 application

Finally make sure you download the **shared** builds, not the static or the
dev builds.

For Mac OS and Linux, the library is usually already installed system-wide.
It may be easiest to list FFmpeg as a requirement for your project,
and leave it up to the user to ensure that it is installed.
For Windows users, it's not recommended to install the library in one of the
windows sub-folders.

Instead we recommend to use the :py:data:`pyglet.options`
``search_local_libs``::

    import pyglet
    pyglet.options['search_local_libs'] = True

This will allow pyglet to find the FFmpeg binaries in the ``lib`` sub-folder
located in your running script folder.

Another solution is to manipulate the environment variable. On Windows you can
add the dll location to the PATH::

    os.environ["PATH"] += "path/to/ffmpeg"

For Linux and Mac OS::

    os.environ["LD_LIBRARY_PATH"] += ":" + "path/to/ffmpeg"

..note:: If your project is going to reply on FFmpeg, it's a good idea to
         check at runtime that FFmpeg is being properly detected. This can be
         done with a call to :py:func:`pyglet.media.have_ffmpeg`. If not `True`
         you can show a message and exit gracefully, rather than crashing later
         when failing to load media files.


Loading media
-------------

Audio and video files are loaded in the same way, using the
:py:func:`pyglet.media.load` function, providing a filename::

    source = pyglet.media.load('explosion.wav')

If the media file is bundled with the application, consider using the
:py:mod:`~pyglet.resource` module (see :ref:`guide_resources`).

The result of loading a media file is a
:py:class:`~pyglet.media.Source` object. This object provides useful
information about the type of media encoded in the file, and serves as an
opaque object used for playing back the file (described in the next section).

The :py:func:`~pyglet.media.load` function will raise a
:py:class:`~pyglet.media.exceptions.MediaException` if the format is unknown.
``IOError`` may also be raised if the file could not be read from disk.
Future versions of pyglet will also support reading from arbitrary file-like
objects, however a valid filename must currently be given.

The length of the media file is given by the
:py:class:`~pyglet.media.Source.duration` property, which returns the media's
length in seconds.

Audio metadata is provided in the source's
:py:attr:`~pyglet.media.Source.audio_format` attribute, which is ``None`` for
silent videos. This metadata is not generally useful to applications. See
the :py:class:`~pyglet.media.AudioFormat` class documentation for details.

Video metadata is provided in the source's
:py:attr:`~pyglet.media.Source.video_format` attribute, which is ``None`` for
audio files. It is recommended that this attribute is checked before
attempting play back a video file -- if a movie file has a readable audio
track but unknown video format it will appear as an audio file.

You can use the video metadata, described in a
:py:class:`~pyglet.media.VideoFormat` object, to set up display of the video
before beginning playback. The attributes are as follows:

    .. list-table::
        :header-rows: 1

        * - Attribute
          - Description
        * - ``width``, ``height``
          - Width and height of the video image, in pixels.
        * - ``sample_aspect``
          - The aspect ratio of each video pixel.

You must take care to apply the sample aspect ratio to the video image size
for display purposes. The following code determines the display size for a
given video format::

    def get_video_size(width, height, sample_aspect):
        if sample_aspect > 1.:
            return width * sample_aspect, height
        elif sample_aspect < 1.:
            return width, height / sample_aspect
        else:
            return width, height

Media files are not normally read entirely from disk; instead, they are
streamed into the decoder, and then into the audio buffers and video memory
only when needed. This reduces the startup time of loading a file and reduces
the memory requirements of the application.

However, there are times when it is desirable to completely decode an audio
file in memory first. For example, a sound that will be played many times
(such as a bullet or explosion) should only be decoded once. You can instruct
pyglet to completely decode an audio file into memory at load time::

    explosion = pyglet.media.load('explosion.wav', streaming=False)

The resulting source is an instance of :class:`~pyglet.media.StaticSource`,
which provides the same interface as a :class:`~pyglet.media.StreamingSource`.
You can also construct a :class:`~pyglet.media.StaticSource` directly from an
already- loaded :class:`~pyglet.media.Source`::

    explosion = pyglet.media.StaticSource(pyglet.media.load('explosion.wav'))

Audio Synthesis
---------------

In addition to loading audio files, the :py:mod:`pyglet.media.synthesis`
module is available for simple audio synthesis. There are several basic
waveforms available, including:

* :py:class:`~pyglet.media.synthesis.Sine`
* :py:class:`~pyglet.media.synthesis.Square`
* :py:class:`~pyglet.media.synthesis.Sawtooth`
* :py:class:`~pyglet.media.synthesis.Triangle`
* :py:class:`~pyglet.media.synthesis.WhiteNoise`
* :py:class:`~pyglet.media.synthesis.Silence`

These waveforms can be constructed by specifying a duration, frequency,
and sample rate. At a minimum, a duration is required. For example::

    sine = pyglet.media.synthesis.Sine(3.0, frequency=440, sample_rate=44800)

For shaping the waveforms, several simple envelopes are available.
These envelopes affect the amplitude (volume), and can make for more
natural sounding tones. You first create an envelope instance,
and then pass it into the constructor of any of the above waveforms.
The same envelope instance can be passed to any number of waveforms,
reducing duplicate code when creating multiple sounds.
If no envelope is used, all waveforms will default to the FlatEnvelope
of maximum amplitude, which esentially has no effect on the sound.
Check the module documentation of each Envelope to see which parameters
are available.

* :py:class:`~pyglet.media.synthesis.FlatEnvelope`
* :py:class:`~pyglet.media.synthesis.LinearDecayEnvelope`
* :py:class:`~pyglet.media.synthesis.ADSREnvelope`
* :py:class:`~pyglet.media.synthesis.TremoloEnvelope`

An example of creating an envelope and waveforms::

    adsr = pyglet.media.synthesis.ADSREnvelope(attack=0.05, decay=0.2, release=0.1)
    saw = pyglet.media.synthesis.Sawtooth(duration=1.0, frequency=220, envelope=adsr)

The waveforms you create with the synthesis module can be played like any
other loaded sound. See the next sections for more detail on playback.

Simple audio playback
---------------------

Many applications, especially games, need to play sounds in their entirety
without needing to keep track of them. For example, a sound needs to be
played when the player's space ship explodes, but this sound never needs to
have its volume adjusted, or be rewound, or interrupted.

pyglet provides a simple interface for this kind of use-case. Call the
:meth:`~pyglet.media.Source.play` method of any :class:`~pyglet.media.Source`
to play it immediately and completely::

    explosion = pyglet.media.load('explosion.wav', streaming=False)
    explosion.play()

You can call :py:meth:`~pyglet.media.Source.play` on any
:py:class:`~pyglet.media.Source`, not just
:py:class:`~pyglet.media.StaticSource`.

The return value of :py:meth:`~pyglet.media.Source.play` is a
:py:class:`~pyglet.media.player.Player`, which can either be
discarded, or retained to maintain control over the sound's playback.

Controlling playback
--------------------

You can implement many functions common to a media player using the
:py:class:`~pyglet.media.player.Player`
class. Use of this class is also necessary for video playback. There are no
parameters to its construction::

    player = pyglet.media.Player()

A player will play any source that is *queued* on it. Any number of sources
can be queued on a single player, but once queued, a source can never be
dequeued (until it is removed automatically once complete). The main use of
this queueing mechanism is to facilitate "gapless" transitions between
playback of media files.

The :py:meth:`~pyglet.media.player.Player.queue` method is used to queue
a media on the player - a :py:class:`~pyglet.media.StreamingSource` or a
:py:class:`~pyglet.media.StaticSource`. Either you pass one instance, or you
can also pass an iterable of sources. This provides great flexibility. For
instance, you could create a generator which takes care of the logic about
what music to play::

    def my_playlist():
       yield intro
       while game_is_running():
          yield main_theme
       yield ending

    player.queue(my_playlist())

When the game ends, you will still need to call on the player::

    player.next_source()

The generator will pass the ``ending`` media to the player.

A :py:class:`~pyglet.media.StreamingSource` can only ever be queued on one
player, and only once on that player. :py:class:`~pyglet.media.StaticSource`
objects can be queued any number of times on any number of players. Recall
that a :py:class:`~pyglet.media.StaticSource` can be created by passing
``streaming=False`` to the :py:func:`pyglet.media.load` method.

In the following example, two sounds are queued onto a player::

    player.queue(source1)
    player.queue(source2)

Playback begins with the player's :py:meth:`~pyglet.media.Player.play` method
is called::

    player.play()

Standard controls for controlling playback are provided by these methods:

    .. list-table::
        :header-rows: 1

        * - Method
          - Description
        * - :py:meth:`~pyglet.media.Player.play`
          - Begin or resume playback of the current source.
        * - :py:meth:`~pyglet.media.Player.pause`
          - Pause playback of the current source.
        * - :py:meth:`~pyglet.media.Player.next_source`
          - Dequeue the current source and move to the next one immediately.
        * - :py:meth:`~pyglet.media.Player.seek`
          - Seek to a specific time within the current source.

Note that there is no `stop` method. If you do not need to resume playback,
simply pause playback and discard the player and source objects. Using the
:meth:`~pyglet.media.Player.next_source` method does not guarantee gapless
playback.

There are several properties that describe the player's current state:

    .. list-table::
        :header-rows: 1

        * - Property
          - Description
        * - :py:attr:`~pyglet.media.Player.time`
          - The current playback position within the current source, in
            seconds. This is read-only (but see the :py:meth:`~pyglet.media.Player.seek` method).
        * - :py:attr:`~pyglet.media.Player.playing`
          - True if the player is currently playing, False if there are no
            sources queued or the player is paused. This is read-only (but
            see the :py:meth:`~pyglet.media.Player.pause` and :py:meth:`~pyglet.media.Player.play` methods).
        * - :py:attr:`~pyglet.media.Player.source`
          - A reference to the current source being played. This is
            read-only (but see the :py:meth:`~pyglet.media.Player.queue` method).
        * - :py:attr:`~pyglet.media.Player.volume`
          - The audio level, expressed as a float from 0 (mute) to 1 (normal
            volume). This can be set at any time.
        * - :py:attr:`~pyglet.media.player.Player.loop`
          - ``True`` if the current source should be repeated when reaching
            the end. If set to ``False``, playback will continue to the next
            queued source.


When a player reaches the end of the current source, an :py:meth:`~pyglet.media.Player.on_eos`
(on end-of-source) event is dispatched. Players have a default handler for this event,
which will either repeat the current source (if the :py:attr:`~pyglet.media.player.Player.loop`
attribute has been set to ``True``), or move to the next queued source immediately.
When there are no more queued sources, the :py:meth:`~pyglet.media.Player.on_player_eos`
event is dispached, and playback stops until another source is queued.

For loop contol you can change the :py:attr:`~pyglet.media.player.Player.loop` attribute
at any time, but be aware that unless sufficient time is given for the future
data to be decoded and buffered there may be a stutter or gap in playback.
If set well in advance of the end of the source (say, several seconds), there
will be no disruption.

The end-of-source behavior can be further customized by setting your own event handlers;
see :ref:`guide_events`. You can either replace the default event handlers directly,
or add an additional event as described in the reference. For example::

    my_player.on_eos = my_player.pause


Gapless playback
----------------

To play back multiple similar sources without any audible gaps,
:py:class:`~pyglet.media.SourceGroup` is provided.
A :py:class:`~pyglet.media.SourceGroup` can only contain media sources
with identical audio or video format. First create an instance of
:py:class:`~pyglet.media.SourceGroup`, and then add all desired additional
sources with the :func:`~pyglet.media.SourceGroup.add` method.
Afterwards, you can queue the :py:class:`~pyglet.media.SourceGroup`
on a Player as if it was a single source.

Incorporating video
-------------------

When a :py:class:`~pyglet.media.player.Player` is playing back a source with
video, use the :attr:`~pyglet.media.Player.texture` property to obtain the
video frame image. This can be used to display the current video image
syncronised with the audio track, for example::

    @window.event
    def on_draw():
        player.texture.blit(0, 0)

The texture is an instance of :class:`pyglet.image.Texture`, with an internal
format of either ``GL_TEXTURE_2D`` or ``GL_TEXTURE_RECTANGLE_ARB``. While the
texture will typically be created only once and subsequentally updated each
frame, you should make no such assumption in your application -- future
versions of pyglet may use multiple texture objects.

Positional audio
----------------

pyglet includes features for positioning sound within a 3D space. This is
particularly effective with a surround-sound setup, but is also applicable to
stereo systems.

A :py:class:`~pyglet.media.player.Player` in pyglet has an associated position
in 3D space -- that is, it is equivalent to an OpenAL "source". The properties
for setting these parameters are described in more detail in the API
documentation; see for example :py:attr:`~pyglet.media.Player.position` and
:py:attr:`~pyglet.media.Player.pitch`.

A "listener" object is provided by the audio driver. To obtain the listener
for the current audio driver::

    pyglet.media.get_audio_driver().get_listener()

This provides similar properties such as
:py:attr:`~pyglet.media.listener.AbstractListener.position`,
:py:attr:`~pyglet.media.listener.AbstractListener.forward_orientation` and
:py:attr:`~pyglet.media.listener.AbstractListener.up_orientation` that
describe the  position of the user in 3D space.

Note that only mono sounds can be positioned. Stereo sounds will play back as
normal, and only their volume and pitch properties will affect the sound.

Ticking the clock
-----------------

If you are using pyglet's media libraries outside of a pyglet app, you will need 
to use some kind of loop to tick the pyglet clock periodically (perhaps every 
200ms or so), otherwise only the first small sample of media will be played::

    pyglet.clock.tick()

If you wish to have a media source loop continuously (`player.loop = True`) you will
also need to ensure Pyglet's events are dispatched inside your loop::

    pyglet.app.platform_event_loop.dispatch_posted_events()

If you are inside a pyglet app then calling `pyglet.app.run()` takes care of 
all this for you.
