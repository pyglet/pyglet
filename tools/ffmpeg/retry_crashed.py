"""
Usage

    retry_crashed.py [--clean] [max_retries]

Inspects the raw data collected to get the list of samples that crashed the last
time they were played.
Then it replays those samples, recording new raw data for them.

The process is repeated until all samples has a recording with no crashes or
the still crashing samples were played 'max_tries' times in this command run.

A configuration must be active, see command configure.py

Besides the updated debug recordings, a state is build and saved:
    total_retries: total retries attempted, including previous runs
    sometimes_crashed: list of samples that crashed one time but later completed a play
    always_crashed: list of samples that always crashed

Options:
    --clean: discards crash data collected in a previous run
    max_retries: defaults to 5
"""
import os
import sys

import fs
from pyglet.media import instrumentation as ins
import mpexceptions
import playmany


def main(clean, max_retries):
    try:
        pathserv = fs.get_path_info_for_active_session()
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined.")
        return 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session active.")
        return 1

    if clean:
        crashes_light_file = pathserv.special_raw_filename("crashes_light")
        if os.path.isfile(crashes_light_file):
            os.unlink(crashes_light_file)

    retry_crashed(pathserv, max_retries)
    return 0


def retry_crashed(pathserv, max_retries=5):
    crashes_light_file = pathserv.special_raw_filename("crashes_light")
    if os.path.isfile(crashes_light_file):
        total_retries, sometimes_crashed, still_crashing = fs.pickle_load(crashes_light_file)
        samples_to_consider = still_crashing
    else:
        total_retries, sometimes_crashed = 0, set()
        playlist_gen = pathserv.session_playlist_generator()
        samples_to_consider = [s for s, f in playlist_gen]

    cnt_retries = 0
    while 1:
        still_crashing = set()
        for sample in samples_to_consider:
            if sample_crashed(pathserv, sample):
                sometimes_crashed.add(sample)
                still_crashing.add(sample)
        fs.pickle_save((total_retries, sometimes_crashed, still_crashing), crashes_light_file)

        if cnt_retries >= max_retries or len(still_crashing) == 0:
            break
        samples_to_consider = still_crashing
        playlist = pathserv.playlist_generator_from_samples_iterable(samples_to_consider)
        playmany.core_play_many(pathserv, playlist)
        cnt_retries += 1
        total_retries += 1


def sample_crashed(pathserv, sample):
    dbg_file = pathserv.dbg_filename(sample)
    log_entries = fs.pickle_load(dbg_file)
    return ins.crash_detected(log_entries)


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) > 1 and sys.argv[1].startswith("--help"):
        print(__doc__)
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        sys.argv.pop(1)
        clean = True
    else:
        clean = False

    if len(sys.argv) > 1:
        max_retries = int(sys.argv[1])
    else:
        max_retries = 5

    return clean, max_retries

if __name__ == "__main__":
    clean, max_retries = sysargs_to_mainargs()
    main(clean, max_retries)
