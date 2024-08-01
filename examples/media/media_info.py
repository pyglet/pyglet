"""Print details of a media file that pyglet can open (requires FFmpeg).

Usage::

    media_info.py <filename>

"""
import sys
import pyglet


def print_ffmpeg_info():
    from pyglet.media import have_ffmpeg

    if have_ffmpeg():
        from pyglet.media.codecs import ffmpeg
        print(f'Using FFmpeg version {ffmpeg.get_version()}')
    else:
        print('FFmpeg not available')
        print('https://www.ffmpeg.org/download.html\n')


def print_source_info(source):
    if source.info:
        if source.info.title:
            print(f'Title: {source.info.title}')
        if source.info.album:
            print(f'Album: {source.info.album}')
        if source.info.author:
            print(f'Author: {source.info.author}')
        if source.info.year:
            print(f'Year: {source.info.year}')
        if source.info.track:
            print(f'Track: {source.info.track}')
        if source.info.genre:
            print(f'Genre: {source.info.genre}')
        if source.info.copyright:
            print(f'Copyright: {source.info.copyright}')
        if source.info.comment:
            print(f'Comment: {source.info.comment}')

    if source.audio_format:
        af = source.audio_format
        print(f'Audio: {af.channels} channel(s), {af.sample_size} bits, {af.sample_rate:.02f} Hz')

    if source.video_format:
        vf = source.video_format
        if vf.frame_rate:
            frame_rate = f'{vf.frame_rate:.02f}'
        else:
            frame_rate = 'unknown'
        if vf.sample_aspect >= 1:
            display_width = vf.sample_aspect * vf.width
            display_height = vf.height
        else:
            display_width = vf.width
            display_height = vf.sample_aspect / vf.height
        print(f'Video: {vf.width}x{vf.height} at aspect {vf.sample_aspect!r} (displays at {display_width}x{display_height}), {frame_rate} fps')

    hours = int(source.duration / 3600)
    minutes = int(source.duration / 60) % 60
    seconds = int(source.duration) % 60
    milliseconds = int(source.duration * 1000) % 1000
    print(f'Duration: {hours}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        print_ffmpeg_info()
        sys.exit(1)

    print_ffmpeg_info()

    filename = sys.argv[1]
    try:
        source = pyglet.media.load(filename, streaming=True)
        print_source_info(source)
        del source
    except pyglet.media.codecs.MediaException:
        print(f'Codec not available to open: {filename}')
