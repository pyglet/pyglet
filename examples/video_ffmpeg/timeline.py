"""
Usage

    timeline.py sample [output_format]

Renders the media player's debug info to a format more suitable to postprocess
in a spreadsheets or other software, particularly to get a data visualization.

See output details in the manual.

Arguments
    sample: sample to report
    output_format : one of { "csv", "pkl"}, by default saves as .pkl (pickle)

The output will be written to session's output dir under
    reports/sample.timeline.[.pkl or .csv]

Example

    timeline.py small.mp4

will write the output to report/small.mp4.timeline.pkl

NOTE: .csv sample is currently not implemented
"""

import sys

import instrumentation as ins
import fs
import mpexceptions


def usage():
    print(__doc__)
    sys.exit(1)


def main(sample, output_format):
    try:
        pathserv = fs.get_path_info_for_active_session()
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined.")
        return 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session active.")
        return 1

    try:
        save_timeline(pathserv, sample, output_format)
    except mpexceptions.ExceptionUnknownOutputFormat as ex:
        print("*** Error, unknown output_format: %s" % output_format)
    return 0


def save_timeline(pathserv, sample, output_format):
    dbg_file = pathserv.dbg_filename(sample)
    recorded_events = fs.pickle_load(dbg_file)
    tm = ins.TimelineBuilder(recorded_events, events_definition=ins.mp_events)
    timeline = tm.get_timeline()
    v = ins.timeline_postprocessing(timeline)
    if output_format == ".pkl":
        outfile = pathserv.report_filename(sample, "timeline.pkl", False)
        fs.pickle_save(v, outfile)
    elif output_format == ".csv":
        outfile = pathserv.report_filename(sample, "timeline.csv", False)
        #? todo: investigate packing multiple tables
        raise NotImplemented
    else:
        raise mpexceptions.ExceptionUnknownOutputFormat(output_format)


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) < 2:
        usage()
    if sys.argv[1].startswith("--"):
        a = sys.argv.pop(1)
        if a.startswith("--help"):
            usage()
        else:
            print("Error unknown option:", a)
            usage()

    if len(sys.argv) < 2:
        print("*** Error, missing argument.\n")
        usage()
    sample = sys.argv.pop(1)

    output_format = ".pkl"
    if len(sys.argv) > 1:
        output_format = sys.argv.pop(1)

    return sample, output_format

if __name__ == '__main__':
    sample, output_format = sysargs_to_mainargs()
    main(sample, output_format)
