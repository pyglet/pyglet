Media manual
^^^^^^^^^^^^

Domain knowledge
================

This tutorial http://dranger.com/ffmpeg/ffmpeg.html is a good intro for
building some domain knowledge. Bear in mind that the tutorial is rather old,
and some ffmpeg functions have become deprecated - but the basics are still
valid.

In the FFmpeg base code there is the ffplay.c player - a very good way to see
how things are managed. In particular, some newer FFmpeg functions are used,
while current pyglet media code still uses functions that have now been
deprecated.

Current code architecture
=========================

The overview of the media code is the following:

Source
------

Found in media/sources folder.

:class:`~pyglet.media.Source` s represent data containing media
information. They can come from disk or be created in memory. A
:class:`~pyglet.media.Source` 's responsibility is to read or generate audio
and/or video data and then provide it. Essentially, it's a *producer*.

FFmpegStreamingSource
---------------------

One implementation of the :class:`~pyglet.media.StreamingSource` is the
``FFmpegSource``. It implements the :class:`~pyglet.media.Source` base class
by calling FFmpeg functions wrapped by ctypes and found in
media/sources/ffmpeg_lib. They offer basic functionalities for handling media
streams, such as opening a file, reading stream info, reading a packet, and
decoding audio and video packets.

The :class:`~pyglet.media.sources.ffmpeg.FFmpegSource` maintains two queues,
one for audio packets and one for video packets, with a pre-determined maximum
size. When the source is loaded, it will read packets from the stream and will
fill up the queues until one of them is full. It has then to stop because we
never know what type of packet we will get next from the stream. It could be a
packet of the same type as the filled up queue, in  which case we would not be
able to store the additional packet.

Whenever a :class:`~pyglet.media.player.Player` - a consumer of a source -
asks for audio data or a video frame, the
:class:`~pyglet.media.Source` will pop the next packet from the
appropriate queue, decode the data, and return the result to the Player. If
this results in available space in both audio and video queues, it will read
additional packets until one of the queues is full again.

Player
------

Found in media/player.py

The :class:`~pyglet.media.player.Player` is the main object that drives the
source.  It maintains an internal sequence of sources or iterator of sources
that it can play sequentially. Its responsibilities are to play, pause and seek
into the source.

If the source contains audio, the :class:`~pyglet.media.player.Player` will
instantiate an ``AudioPlayer`` by asking the ``AudioDriver`` to create an
appropriate ``AudioPlayer`` for the given platform. The ``AudioDriver`` is a
singleton created according to which drivers are available. Currently
supported sound drivers are: DirectSound, OpenAL, PulseAudio and XAudio2.
A silent audio driver that consumes, but does not play back any audio is also
available.

If the source contains video, the Player has a
:meth:`~pyglet.media.Player.get_texture` method returning the current
video frame.

The player has an internal `master clock` which is used to synchronize the
video and the audio. The audio synchronization is delegated to the
``AudioPlayer``. More info found below. The video synchronization is made by
asking the :class:`~pyglet.media.Source` for the next video timestamp.
The :class:`~pyglet.media.player.Player` then schedules on pyglet event loop a
call to its :meth:`~pyglet.media.Player.update_texture` with a delay
equals to the difference between the next video timestamp and the master clock
current time.

When :meth:`~pyglet.media.Player.update_texture` is called, we will
check if the actual master clock time is not too late compared to the video
timestamp. This could happen if the loop was very busy and the function could
not be called on time. In this case, the frame would be skipped until we find
a frame with a suitable timestamp for the current master clock time.

AudioPlayer
-----------

Found in media/drivers

The ``AudioPlayer`` is responsible for playing the audio data. It reads
from the :class:`~pyglet.media.Source`, and can be started, stopped or cleared.

In order to accomplish this task, the audio player keeps a reference to the
``AudioDriver`` singleton which provides access to the lower level functions
for the selected audio driver, and its ``Player``, which it synchronizes with
and dispatches events to.

``AudioPlayer`` s are bound to their source's
:class:`~pyglet.media.AudioFormat`. Once created, they can not play audio of
a different format.

``AudioPlayer`` s will attempt to keep themselves in sync with their associated
``Player`` . This is achieved by the ``_get_and_compensate_audio_data`` method.
The last 8 differences between their estimated audio time and their player's
master clock will be stored for each read chunk of audio data.
If the average of this value exceeds a value of 30ms, the player will start to
correct itself by either dropping or duplicating a very small amount of
samples at a time, 12ms by default.
If any single measurement exceeds 280ms, an extreme desync that is noticeable
in context of the app is assumed. If the ``AudioPlayer`` is running behind the
master clock, all of this audio data is skipped and the measurements are reset.
When running *ahead* by more than 280ms, nothing is done but the standard
stretchin g of 12ms at a time.

.. _audioplayer-play:

``play``
""""""""

When instructed to play, the ``AudioPlayer`` will give whatever instructions
are necessary to its audio backend in order to start playing itself.

To not run out of data, it will add itself into the ``PlayerWorkerThread`` of
its audio driver. This thread is typically responsible for asking sources for
audio data to prevent the main thread/event loop from locking up on I/O
operations. The ``PlayerWorkerThread`` will regularly call
:ref:`audioplayer-work` on each ``AudioPlayer``.

This method may be called when already playing, and has no effect in that case.

.. _audioplayer-stop:

``stop``
""""""""

This method causes the ``AudioPlayer`` to stop playing its audio stream, or to
pause it. It may be restarted with :ref:`audioplayer-play` later-on, which will
cause it to continue from where it stopped.

The first thing this method should do is to remove itself from its driver's
``PlayerWorkerThread`` to ensure :ref:`audioplayer-work` won't be called while
it stops.

This method may be called when already stopped, and has no effect in that case.

.. _audioplayer-prefill_audio:

``prefill_audio``
"""""""""""""""""

This method is called from a ``Player`` whenever the ``AudioPlayer`` is about
to start playing and also before :ref:`audioplayer-play` is called for the
first time. The first batch of data is given from here, as backends using a
single audio buffer may play undefined data for a short amount of time before
the ``PlayerWorkerThread`` would load proper audio data in.

This method prefills the ideal amount of data for an ``AudioPlayer``, available
in ``_buffered_data_ideal_size``. By default this is given as 900ms of audio,
depending on the played source's audio format.

.. _audioplayer-work:

``work``
""""""""

This method is only called from a ``PlayerWorkerThread``, though it may be
invoked through :ref:`audioplayer-prefill_audio`. As it is called from a
thread, implementing it error-free is difficult.

This method is responsible for refilling audio data if needed and often for
dispatching the :meth:`~pyglet.media.player.Player.on_eos` event.

Implementing this method comes with a lot of pitfalls. The following are free
to happen in other threads while the method is running:

The player is paused or unpaused.
    Audio backends usually accept data for non-playing streams/sources/etc.,
    so this is not too much of a problem. Realistically, this won't happen, all
    current implementations contain a call to
    ``self.driver.worker.remove/add(self)`` snippet in their
    :ref:`audioplayer-play`/:ref:`audioplayer-stop` implementations.
    That call will return only once the ``PlayerWorkerThread`` is done with a
    work cycle.

    In order for these calls to be most reliable, ``remove`` should be the
    first statement in a :ref:`audioplayer-stop` implementation and ``add``
    the last one in a :ref:`audioplayer-play` implementation, to ensure that
    :ref:`audioplayer-work` will not be run after/will not start before player
    attributes have been changed.

The player is deleted.
    In order to combat this, ``self.driver.worker.remove(self)`` is used in all
    implementations, ensuring delete calls will not interfere with the
    :ref:`audioplayer-work` method.

A native callback runs, changing the internal state of the ``AudioPlayer``.
    See below; protecting some sections with a lock local to the
    ``AudioPlayer``. This lock should not be held around the call to
    ``_get_and_compensate_audio_data``, as that renders the entire step of
    offloading the loading/decoding work into a ``PlayerWorkerThread``
    obsolete.

In pseudocode, the general way this method is implemented is: ::

    def work():
        update_play_cursor()
        dispatch_media_events()
        if not source_exhausted:
            if play_cursor_too_close_to_write_cursor():
                get_and_submit_new_audio_data()
                if source_exhausted:
                    update_play_cursor()
                else:
                    return
            else:
                return
        if play_cursor > write_cursor and not has_underrun:
            has_underrun = True
            dispatch_on_eos()

If native callbacks are involved, running in yet another thread, the flow
tends to be different: ::

    def work():
        update_play_cursor()
        dispatch_media_events()
        if not source_exhausted:
            if play_cursor_too_close_to_write_cursor():
                get_and_submit_new_audio_data()
                if has_underrun:
                    if source_exhausted:
                        dispatch_eon_eos()
                    else:
                        restart_player()
                        has_underrun = False

    def on_underrun():
        if source_exhausted:
            dispatch_on_eos()
        else:
            has_underrun = True

High care must be taken to protect appropiate sections (any variables and
buffers which get accessed by both callbacks and the work method) with a lock,
otherwise the method is open to extremely unlucky issues where the callback
is unscheduled in favor of the work method or vice versa, which may cause one
of the functions to assume/operate based on a now outdated state.

``work`` won't stop being called just because it dispatched ``on_eos``. The
method must make sure its source did not run out of audio data before to only
dispatch this event once.

.. _audioplayer-clear:

``clear``
"""""""""

This method may *only* be called when the ``AudioPlayer`` is not playing.
It causes it to discard all buffered data and reset itself to a clean initial
state.

``delete``
""""""""""

This method will cause the ``AudioPlayer`` to stop playing and delete all its
native resources. In contrast to :ref:`audioplayer-clear`, it may be called at
any time. It may be called multiple times and must make sure it won't delete
already deleted resources.

AudioDriver
-----------

Found in media/drivers

The ``AudioDriver`` is a wrapper around the low-level sound driver available
on the platform. It's a singleton. It can create an ``AudioPlayer``
appropriate for the current ``AudioDriver``.

The ``AudioDriver`` usually contains a ``PlayerWorkerThread`` responsible for
keeping each ``AudioPlayer`` that is playing filled with data.

The ``AudioDriver`` provides an ``AudioListener``, which is used to place
a listener in the same space as each ``AudioPlayer``, enabling positional
audio.

Normal operation of the ``Player``
----------------------------------

The client code instantiates a media player this way::

    player = pyglet.media.Player()
    source = pyglet.media.load(filename)
    player.queue(source)
    player.play()

When the client code runs ``player.play()``:

The :class:`~pyglet.media.player.Player` will check if there is an audio track
on the media. If so it will instantiate an ``AudioPlayer`` appropriate for the
available sound driver on the platform. It will create an empty
:class:`~pyglet.image.Texture` if the media contains video frames and will
schedule its :meth:`~pyglet.media.Player.update_texture` to be called
immediately. Finally it will start the master clock.

The ``AudioPlayer`` will start playing
:ref:`as described above <audioplayer-play>`.

When the :meth:`~pyglet.media.Player.update_texture` method is called,
the next video timestamp will be checked with the master clock. We allow a
delay up to the frame duration. If the master clock is beyond that time, the
frame will be skipped. We will check the following frames for its timestamp
until we find the appropriate frame for the master clock time. We will set the
:attr:`~pyglet.media.player.Player.texture` to the new video frame. We will
check for the next video frame timestamp and we will schedule a new call to
:meth:`~pyglet.media.Player.update_texture` with a delay equals to the
difference between the next video timestamps and the master clock time.

Helpful tools
=============

I've found that using the binary ffprobe is a good way to explore the content
of a media file. Here's a couple of things which might be
interesting and helpful::

    ffprobe samples_v1.01\SampleVideo_320x240_1mb.3gp -show_frames

This will show information about each frame in the file. You can choose only
audio or only video frames by using the ``v`` flag for video and ``a`` for
audio.::

    ffprobe samples_v1.01\SampleVideo_320x240_1mb.3gp -show_frames -select_streams v


You can also ask to see a subset of frame information this way::

    ffprobe samples_v1.01\SampleVideo_320x240_1mb.3gp -show_frames
    -select_streams v -show_entries frame=pkt_pts,pict_type

Finally, you can get a more compact view with the additional ``compact`` flag:

    ffprobe samples_v1.01\SampleVideo_320x240_1mb.3gp -show_frames
    -select_streams v -show_entries frame=pkt_pts,pict_type -of compact

Convert video to mkv
====================

::

    ffmpeg -i <original_video> -c:v libx264 -preset slow -profile:v high -crf 18
    -coder 1 -pix_fmt yuv420p -movflags +faststart -g 30 -bf 2 -c:a aac -b:a 384k
    -profile:a aac_low <outputfilename.mkv>
