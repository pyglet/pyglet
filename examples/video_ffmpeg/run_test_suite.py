"""
Usage

    run_test_suite.py [samples_dir]

Plays media samples with the pyglet media_player, recording debug information
for each sample played and writing reports about the data captured.

Arguments
    samples_dir: directory with the media samples to play

If no sample_dir is provided the samples to play will come from the active
session (see cmd configure new)

If the samples_dir is provided, all files whitin will be played except for the
ones with extension ".dbg", ".htm", ".html", ".json", ".log", ".pkl", ".py",
".txt" ; subdirectories of samples_dir will not be explored. 

Output files will be into
    samples_dir/testrun/dbg : binary capture of media_player events
    samples_dir/testrun/reports : human readable reports

(with testrun provided by the active session if sample_dir was not provided)
"""

import os
import sys

import fs
import instrumentation as ins
import playmany
import retry_crashed
import summarize


def main(samples_dir):
    if samples_dir is None:
        # get from active session
        pathserv = fs.get_path_info_for_active_session()
    else:
        # create a session with a default name, provide a pathserv
        session = None
        for i in range(100):
            name = "testrun_%02d" % i
            if not os.path.exists(os.path.join(samples_dir, name)):
                session = name
                pathserv = fs.new_session_for_samples_dir(session, samples_dir)
                break
        if session is None:
            s = os.path.join(samples_dir, "testrun_n")
            print("*** Error, failed to create output dir in the form %s , for any n<100." % s)
            sys.exit(1)

    print("Results will be write to directory: % s" % pathserv.session_dir)

    playmany.play_many(pathserv)

    retry_crashed.retry_crashed(pathserv)

    count_bads = ins.CountBads()
    summarize.summarize(pathserv, count_bads)

    # protect raw data and reports
    modify = {
        "protect_raw_data": True,
        "protect_reports": True,
        }
    fs.update_configuration(pathserv, modify)
    
    print("*** done ***") 


def usage():
    print(__doc__)
    sys.exit(1)


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) > 1:
        for i in range(1):
            if sys.argv[1].startswith("--"):
                a = sys.argv.pop(1)
                if a.startswith("--help"):
                    usage()
                else:
                    print("Error unknown option:", a)
                    usage()

    if len(sys.argv) > 1:
        samples_dir = sys.argv.pop(1)
    else:
        samples_dir = None

    if len(sys.argv) > 1:
        print("Error, unexpected extra params: %s ..." % sys.argv[1])
        usage()

    return samples_dir 

if __name__ == '__main__':
    samples_dir = sysargs_to_mainargs()
    main(samples_dir)
