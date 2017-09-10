"""
Usage

    playmany.py

Uses media_player to play a sequence of samples and record debug info

A configuration must be active, see command configure.py
If the active configuration has disallowed dbg overwrites it will do nothing.

If a playlist was provided at session creation, then only the samples in the
playlist will be played, otherwise all files in samples_dir.

"""

import subprocess
import sys

import fs
import mpexceptions


def main():
    try:
        pathserv = fs.get_path_info_for_active_session()
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined.")
        return 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session active.")
        return 1

    try:
        play_many(pathserv, timeout=120)
    except mpexceptions.ExceptionAttemptToBreakRawDataProtection:
        print("*** Error, attempt to overwrite raw data when protect_raw_data is True.")
        return 1

    return 0


def play_many(pathserv, timeout=120):
    """plays the samples in the session playlist for the current active session
       timeout: max time allowed to play a sample, default is 120 seconds
    """
    conf = fs.get_session_configuration(pathserv)
    if conf["dev_debug"]:
        pass
    else:
        if conf["protect_raw_data"]:
            raise mpexceptions.ExceptionAttemptToBreakRawDataProtection()

    playlist_gen = pathserv.session_playlist_generator()
    core_play_many(pathserv, playlist_gen, timeout=timeout)


def core_play_many(pathserv, playlist_gen, timeout=120):
    for sample, filename in playlist_gen:
        dbg_file = pathserv.dbg_filename(sample)

        print("playmany playing:", filename)

        cmdline = ["media_player.py",
                   "--debug",
                   "--outfile=" + dbg_file,
                   filename]
        killed, returncode = cmd__py3(cmdline, timeout=timeout)
        if killed:
            print("WARNING: killed by timeout, file: %s" % filename)


def cmd__py3(cmdline, bufsize=-1, cwd=None, timeout=60):
    """runs a .py script as a subprocess with the same python as the caller

       cmdline: list [<scriptname>, arg1, ...]
       timeout: time in seconds; subprocess wil be killed if it is still running
                at that time.
    """
    # use the same python as the caller to run the script
    cmdline.insert(0, "-u")
    cmdline.insert(0, sys.executable)

    p = subprocess.Popen(
        cmdline,
        bufsize = bufsize,
        shell   = False,
        stdout  = subprocess.PIPE,
        stderr  = subprocess.PIPE,
        cwd     = cwd
    )
    killed = True
    try:
        out, err = p.communicate(timeout=timeout)
        killed = False
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
##    print("out:", out)
##    print("err:", err)

    returncode = p.returncode

    return killed, returncode


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) > 1 and sys.argv[1].startswith("--help"):
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    sysargs_to_mainargs()
    main()
