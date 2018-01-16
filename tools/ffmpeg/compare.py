"""
Usage

    compare.py --reldir=relpath other_session

Builds a reports comparing the active session with other_session.

Outputs to samples_dir/relpath/comparison_<session>_<other_session>.txt
"""
import os
import sys

import extractors
import fs
from pyglet.media import instrumentation as ins
import mpexceptions
import reports


def main(relative_out_dir, other_session):
    try:
        pathserv = fs.get_path_info_for_active_session()
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined.")
        return 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session active.")
        return 1

    try:
        pathserv_other = fs.get_path_info_for_session(other_session)
    except mpexceptions.ExceptionNoSessionWithThatName:
        print("No session by that name")
        return 1

    outdir = os.path.join(fs.get_current_samples_dir(), relative_out_dir)
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    compare_sessions_to_file(pathserv, pathserv_other, outdir)
    return 0


def compare_sessions_to_file(pathserv, pathserv_other, outdir):
    """compares two sessions, outputs text to file
    outdir/comparison_<session>_<other_session>.txt
    """
    outfile = os.path.join(outdir, "comparison_%s_%s.txt" %
                           (pathserv.session, pathserv_other.session))
    text = compare_sessions_to_text(pathserv, pathserv_other)
    fs.txt_save(text, outfile)


def compare_sessions_to_text(pathserv, pathserv_other):
    """compares two sessions, returns text"""
    count_bads = ins.CountBads()
    comparison = extractors.CollectSessionComparisonData(pathserv,
                                                         pathserv_other,
                                                         count_bads.count_bads)
    text = reports.report_session_comparison(comparison)
    return text


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    relative_out_dir = None
    if len(sys.argv) > 1 and sys.argv[1].startswith("--"):
        a = sys.argv.pop(1)
        if a.startswith("--help"):
            print(__doc__)
            sys.exit(1)
        elif a.startswith("--reldir="):
            relative_out_dir = a[len("--reldir="):]
        else:
            print("*** Error, Unknown option:", a)
            print(__doc__)
            sys.exit(1)

    other_session = sys.argv[1]
    return relative_out_dir, other_session


if __name__ == "__main__":
    relative_out_dir, other_session = sysargs_to_mainargs()
    main(relative_out_dir, other_session)
