"""
Usage

    summarize.py

Summarizes the session info collected with playmany and retry_crashes

A configuration must be active, see command configure.py

If a playlist was provided at session creation, then only the samples in the
playlist will be played, otherwise all files in samples_dir.
"""

import shutil
import sys

import extractors
import fs
from pyglet.media import instrumentation as ins
import mpexceptions
import report
import reports


def main():
    try:
        pathserv = fs.get_path_info_for_active_session()
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined.")
        return 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session active.")
        return 1

    count_bads = ins.CountBads()

    try:
        summarize(pathserv, count_bads)
    except mpexceptions.ExceptionAttemptToBrekReportsProtection:
        print("*** Error, attempt to overwrite reports when protect_reports "
              "is True.")
        return 1
    except mpexceptions.ExceptionNoDbgFilesPresent:
        print("*** Error, no dbg files present; maybe playmany should be run?")
        return 1
    return 0


def summarize(pathserv, count_bads):
    conf = fs.get_session_configuration(pathserv)
    if conf["dev_debug"]:
        pass
    else:
        if conf["protect_reports"]:
            raise mpexceptions.ExceptionAttemptToBreakRawDataProtection()

    session = pathserv.session
    parts = ["Summary of media_player debug info for session: %s" % session]
    filename = pathserv.special_raw_filename("samples_version")
    try:
        text = fs.txt_load(filename)
    except Exception as ex:
        print(ex)
        print("*** Error, could not read dbg/_version.txt, "
              "target dir probably not a session one.")
        sys.exit(1)
    parts.append("Samples version: %s" % text)

    overall = extractors.single_session_overall_defect_counters(pathserv, count_bads.count_bads)

    if len(overall.no_dbg_samples):
        parts.append("Samples with no .dbg recording: %d" % len(overall.no_dbg_samples))
    else:
        parts.append("All samples have a .dbg recording.")

    if len(overall.crashed_samples):
        parts.append("Samples that always crashed: %d" % len(overall.crashed_samples))
    else:
        parts.append("All samples (finally) got a report with no crash.")

    n = overall.total_relevant_samples()
    parts.append("Relevant samples (all - no_dbg - crashed): %d" % n)

    no_relevant_samples = (n == 0)
    if no_relevant_samples:
        parts.append("*** Error, no relevant samples remains to calculate"
                     " score.")
    else:
        parts.extend([
            "Naive quality number (anomalies / samples): %f" % overall.defects_per_sample(),
            "Relevant samples with perfect play: %d / %d" % (len(overall.perfect_play_samples), n),
            "Relevant samples with anomalies   : %d / %d" % (len(overall.counters_non_perfect_play_samples), n),
            ""
            ])

    # include crash info collected by retry_crashed.py
    text = reports.fragment_crash_retries(pathserv)
    parts.append(text)
    parts.append("")

    # include count of defects for samples with anomalies but no crash
    if len(overall.counters_non_perfect_play_samples):
        parts.append("Per sample defects info (always crashed and perfect plays"
                     " not listed)\n")
        for sample in sorted(overall.counters_non_perfect_play_samples.keys()):
            counters = overall.counters_non_perfect_play_samples[sample]
            text = reports.format_anomalies_counter(
                count_bads.anomalies_description, counters, sample)
            parts.append(text)
            parts.append("")

        # additionally emit reports 'anomalies' and 'all'
        for sample in overall.counters_non_perfect_play_samples.keys():
            report.report_sample(pathserv, sample, "anomalies")
            report.report_sample(pathserv, sample, "all")

    # appendix, list of samples without dbg
    if len(overall.no_dbg_samples):
        parts.append("Appendix, list of samples without dbg")
        for s in overall.no_dbg_samples:
            parts.append("\t%s" % s)
        parts.append("")

    text = "\n".join(parts)
    filename_summary = pathserv.special_report_filename("summary")
    fs.txt_save(text, filename_summary)

    # output pyglet info as captured at session creation
    src = pathserv.special_raw_filename("pyglet_info")
    dst = pathserv.special_report_filename("pyglet_info")
    shutil.copyfile(src, dst)
    src = pathserv.special_raw_filename("pyglet_hg_revision")
    dst = pathserv.special_report_filename("pyglet_hg_revision")
    try:
        shutil.copyfile(src, dst)
    except Exception:
        pass


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) > 1 and sys.argv[1].startswith("--help"):
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
