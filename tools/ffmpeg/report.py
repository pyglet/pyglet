import sys

import reports
import fs
import mpexceptions


def description():
    template = ("""
Usage

    report.py sample report_name

Generates a report from the debugging info recorded while playing sample

Arguments

    sample: sample to report
    report_name: desired report, one of
{reports}

The report will be written to session's output dir under reports/sample.report_name.txt

Example

    report anomalies small.mp4

will write the report 'anomalies' to report/small.mp4.anomalies.txt
"""
                )
    text = template.format(reports=reports.available_reports_description(line_prefix=" " * 8))
    return text


def main(sample, report_name):
    try:
        pathserv = fs.get_path_info_for_active_session()
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined.")
        return 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session active.")
        return 1

    report_sample(pathserv, sample, report_name)


def report_sample(pathserv, sample, report_name):
    dbg_file = pathserv.dbg_filename(sample)
    outfile = pathserv.report_filename(sample, report_name)
    log_entries = fs.pickle_load(dbg_file)
    text = reports.report_by_name(report_name)(log_entries)
    fs.txt_save(text, outfile)


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) < 3:
        print(description())
        sys.exit(1)
    report_name, sample = sys.argv[1:]
    return report_name, sample

if __name__ == '__main__':
    sample, report_name = sysargs_to_mainargs()
    main(sample, report_name)
