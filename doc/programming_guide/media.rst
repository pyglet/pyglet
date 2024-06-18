.. _guide-media:

Playing Sound and Video
=======================

pyglet can load and play many audio and video formats, often with
support for surround sound and video effects.

WAV and MP3 files are the most commonly supported across platforms. The
formats a specific computer can play are determined by which of the
following are available:

#. The built-in pyglet WAV file decoder (always available)
#. Platform-specific APIs and libraries
#. PyOgg
#. :ref:`guide-supportedmedia-ffmpeg` version 4, 5, or 6

Video is played into OpenGL textures, allowing real-time manipulation
by applications. Examples include use in 3D environments or shader-based
effects. To play video, :ref:`guide-supportedmedia-ffmpeg` must be
installed.

Audio is played back with one of the following: OpenAL, XAudio2,
DirectSound, or PulseAudio. Hardware-accelerated mixing is available
on all of them. 3D positional audio and surround sound features are
available on all back-ends other than PulseAudio.

.. _FFmpeg: https://www.ffmpeg.org/download.html
.. _openal.org: https://www.openal.org/downloads

Audio drivers
-------------

pyglet can use OpenAL, XAudio2, DirectSound, or PulseAudio to play
sound. Only one driver can be used at a time, but the selection can
be changed by altering the configuration and restarting the program.

The default driver preference order works well for most users. However,
you may override it by setting a different preference sequence before
the :py:mod:`pyglet.media` module is loaded. See
:ref:`guide-audio-driver-order` to learn more.

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
          - PulseAudio [#pulseaudiof]_

.. [#pulseaudiof] The :ref:`guide-audio-driver-pulseaudio` driver has
     limitations. For audio-intensive programs, consider using
     :ref:`guide-audio-driver-openal`.

.. [#openalf] OpenAL does not come preinstalled on Windows and some
     Linux distributions.

.. _guide-audio-driver-order:

Choosing the audio driver
^^^^^^^^^^^^^^^^^^^^^^^^^

The ``'audio'`` key of the :py:data:`pyglet.options` dictionary
specifies the audio driver preference order.

On import, the :mod:`pyglet.media` will try each entry from first to
last until it either finds a working driver or runs out of entries. For
example, the default is equivalent to setting the following value::

   pyglet.options['audio'] = ('xaudio2', 'directsound', 'openal', 'pulse', 'silent')

You can also set a custom preference order. For example, we could add
this line before importing the media module::

    pyglet.options['audio'] = ('openal', 'pulse', 'xaudio2', 'directsound', 'silent')

It tells pyglet to try using the OpenAL driver first. If is not
available,  try Pulseaudio, XAudio2, and DirectSound in that order.
If all else fails, no driver will be instantiated and the game will
run silently.

The value for the ``'audio'`` key can be a list or tuple which contains
one or more of the following strings:

    .. list-table::
        :header-rows: 1

        * - String
          - Audio driver
        * - ``'openal'``
          - OpenAL
        * - ``'directsound'``
          - DirectSound
        * - ``'xaudio2'``
          - XAudio2
        * - ``'pulse'``
          - PulseAudio
        * - ``'silent'``
          - No audio output

You must set any custom ``'audio'`` preference order before importing
:mod:`pyglet.media`. This can also be set through an environment variable;
see :ref:`guide_environment-settings`.

The following sections describe the requirements and limitations of each audio
driver.

.. _guide-audio-driver-xaudio2:

XAudio2
^^^^^^^
XAudio2 is only available on Windows Vista and above and is the replacement of
DirectSound. This provides hardware accelerated audio support for newer operating
systems.

Note that in some stripped down versions of Windows 10, XAudio2 may not be available
until the required DLL's are installed.

.. _guide-audio-driver-directsound:

DirectSound
^^^^^^^^^^^

DirectSound is available only on Windows, and is installed by default.
pyglet uses only DirectX 7 features. On Windows Vista, DirectSound does not
support hardware audio mixing or surround sound.

.. _guide-audio-driver-openal:

OpenAL
^^^^^^

The favored driver for Mac OS X, but also available on other systems.

This driver has the following advantages:

* Either preinstalled or easy to install on supported platforms.
* Implements features which may be absent from other drivers or
  OS-specific versions of their backing APIs.

Its main downsides are:

* Not guaranteed to be installed on platforms other than Mac OS X
* On recent Windows versions, the :ref:`guide-audio-driver-xaudio2` and
  :ref:`guide-audio-driver-directsound` backends may support more
  features.

Windows users can download an OpenAL implementation from `openal.org`_
or their sound device's manufacturer.

On Linux, the following apply:

* It can usually be installed through your distro's package manager.
* It may already be installed as a dependency of other packages.
* It lacks the limitations of the :ref:`guide-audio-driver-pulseaudio`
  driver.

The commands below should install OpenAL on the most common Linux
distros:

.. list-table::
    :header-rows: 1

    * - Common Linux Distros
      - Install Command

    * - Ubuntu, Pop!_OS, Debian
      - ``apt install libopenal1``

    * - Arch, Manjaro
      - ``pacman -S openal``

    * - Fedora, Nobara
      - ``dnf install openal-soft``

You may need to prefix these commands with either ``sudo`` or another
command. Consult your distro's documentation for more information.

.. _guide-audio-driver-pulseaudio:

PulseAudio
^^^^^^^^^^

This backend is almost always supported, but it has limited features.

If it fails to initialize, consult your distro's documentation to learn
which supported audio back-ends you can install.

Missing features
""""""""""""""""

Although PulseAudio can theoretically support advanced multi-channel
audio, the pyglet driver does not. The following features will not
work properly:

#. Positional audio: automatically changing the volume for individual
   audio channels based on the position of the sound source
#. Integration with surround sound

Switching to :ref:`guide-audio-driver-openal` should automatically enable them.

.. _guide-supportedmedia:

Supported media types
---------------------

pyglet has included support for loading Wave (.wav) files, which are therefore
guaranteed to work on all platforms. pyglet will also use various platform libraries
and frameworks to support a limited amount of compressed audio types, without the need
for FFmpeg. While FFmpeg supports a large array of formats and codecs, it may be an
unnecessarily large dependency when only simple audio playback is needed.

These formats are supported natively under the following systems and codecs:

.. _guide-supportedmedia-wmf:

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

.. _guide-supportedmedia-gstreamer:

GStreamer
^^^^^^^^^
Supported on Linux operating systems that have the GStreamer installed. Please note that the
associated Python packages for gobject & gst are also required. This varies by distribution,
but will often already be installed along with GStreamer.

* MP3
* FLAC
* OGG
* M4A

.. _guide-supportedmedia-coreaudio:

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

.. _guide-supportedmedia-pyogg:

PyOgg
^^^^^

.. _pyogg_install: https://pyogg.readthedocs.io/en/latest/installation.html

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

To install PyOgg, please see their `installation guide on readthedocs.io
<pyogg_install_>`_.

.. _guide-supportedmedia-ffmpeg:

FFmpeg
^^^^^^
.. _FFmpeg's license overview: https://www.ffmpeg.org/legal.html

.. note:: The most recent pyglet release can use FFmpeg 4.X, 5.X, or 6.X

          See :ref:`guide-media-ffmpeginstall` to learn more.

FFmpeg is best when you need to support the maximum number of formats
and encodings. It is also worth considering the following:

* Support for many formats and container types means large download size
* FFmpeg's compile options allow it to be built and used under :ref:`either
  the LGPL or GPL license <guide-ffmpeg-licenses>`

See the following sections to learn more.

See :ref:`guide-ffmpeg-licenses` to learn more.

Supported Formats
"""""""""""""""""

.. _the FFmpeg documentation: https://ffmpeg.org/ffmpeg.html

It is difficult to provide a complete list of FFmpeg's features due to
the large number of audio and video codecs, options, and container
formats it supports. Refer to `the FFmpeg documentation`_ for
more information.

Known supported audio formats include:

* AU
* MP2
* MP3
* OGG/Vorbis
* WAV
* WMA

Known supported video formats include:

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

The easiest way to check whether a file will load through FFmpeg is to
try playing it through the ``media_player.py`` example. New releases of
FFmpeg may fix bugs and add support for new formats.

.. _guide-ffmpeg-licenses:

FFmpeg & licenses
"""""""""""""""""

FFmpeg's code uses different licenses for different parts.

The core of the project uses a modified LGPL license. However, the GPL
is used for certain optional parts. Using these components, as well as
bundling FFmpeg binaries which include them, may require full GPL
compliance. As a result, some organizations may restrict some or all
use of FFmpeg.

pyglet's FFmpeg bindings do not rely on the optional GPL-licensed parts.
Therefore, most projects should be free to use any license they choose
for their own code as long as they use one of the following approaches:

* Require users to install FFmpeg themselves using either:

  * The :ref:`guide-media-ffmpeginstall` section on this page
  * Custom instructions for a specific FFmpeg version

* Make FFmpeg optional as described at the end of the
  :ref:`guide-media-ffmpeginstall` instructions
* Bundle an LGPL-only build of FFmpeg

See the following to learn more:

* `FFmpeg's license overview`_
* The license documentation for your specific FFmpeg version:

  * `The FFmpeg 4.4 license breakdown <https://ffmpeg.org/doxygen/4.4/md_LICENSE.html>`_
  * `The FFmpeg 5.1 license breakdown <https://ffmpeg.org/doxygen/5.1/md_LICENSE.html>`_
  * `The FFmpeg 6.0 license breakdown <https://ffmpeg.org/doxygen/6.0/md_LICENSE.html>`_

.. _guide-media-ffmpeginstall:

FFmpeg installation
-------------------

You can install FFmpeg for your platform by following the instructions found
in the `FFmpeg download <https://www.ffmpeg.org/download.html>`_ page. You must
choose the shared build for the targeted OS with the architecture similar to
the Python interpreter.

All recent pyglet versions support FFmpeg 4.x and 5.x. To use FFmpeg 6.X,
you must use pyglet 2.0.8 or later.

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

.. tip:: Prevent crashes by checking for FFmpeg before loading media!

         Call :py:func:`pyglet.media.have_ffmpeg` to check whether
         FFmpeg was detected correctly. If it returns ``False``, you can
         take an appropriate action instead of crashing. Examples
         include:

         * Showing a helpful error in the GUI or console output
         * Exiting gracefully after the the user clicks OK on a dialog
         * Limiting the formats your project will attempt to load


.. _guide-media-loading:

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


.. _guide-media-audiosynthesis:

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

.. _guide-media-simpleaudioplayback:

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

.. _guide-media-controllingplayback:

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


.. _guide-media-playbackevents:

Handling playback events
------------------------

When a player reaches the end of the current source, an :py:meth:`~pyglet.media.Player.on_eos`
(on end-of-source) event is dispatched. Players have a default handler for this event,
which will either repeat the current source (if the :py:attr:`~pyglet.media.player.Player.loop`
attribute has been set to ``True``), or move to the next queued source immediately.
When there are no more queued sources, the :py:meth:`~pyglet.media.Player.on_player_eos`
event is dispatched, and playback stops until another source is queued.

For loop control you can change the :py:attr:`~pyglet.media.player.Player.loop` attribute
at any time, but be aware that unless sufficient time is given for the future
data to be decoded and buffered there may be a stutter or gap in playback.
If set well in advance of the end of the source (say, several seconds), there
will be no disruption.

The end-of-source behavior can be further customized by setting your own event handlers;
see :ref:`guide_events`. You can either replace the default event handlers directly,
or add an additional event as described in the reference. For example::

    my_player.on_eos = my_player.pause


.. _guide-media-gaplessplayback:

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

.. _guide-media-incorporating_video:

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

.. _guide-media-positionalaudio:

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

.. _guide-media-tickingtheclock:

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
