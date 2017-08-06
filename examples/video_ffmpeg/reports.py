import os

import fs
import instrumentation as ins
import mpexceptions


def render_event(events_definition, state, fn_prefix):
    evname = state["evname"]
    ev_description = events_definition[evname]
    parts = [fn_prefix(state)]
    parts.append(ev_description["desc"])
    for name in ev_description["update_names"]:
        if name == "evname":
            continue
        parts.append(" %s: %s" % (name, state[name]))
    extra_names = ev_description["other_fields"]
    if extra_names:
        parts.append(' ;')
        for name in extra_names:
            parts.append(" %s: %s" % (name, state[name]))
    text = "".join(parts)
    return text


def rpt_all(log_entries, events_definition=ins.mp_events):
    no_indent = {"crash", "mp.im", "p.P._sp", "p.P.sk", "p.P.ut.1.0", "p.P.oe"}
    fn_prefix = lambda st: "" if st["evname"] in no_indent else "    "
    mp_states = ins.MediaPlayerStateIterator(log_entries, events_definition)
    parts = []
    for mp in mp_states:
        s = "%4d " % mp["frame_num"] + render_event(events_definition, mp, fn_prefix)
        parts.append(s)
    text = "\n".join(parts)
    return text


def rpt_anomalies(log_entries, events_definition=ins.mp_events):
    allow = {"crash", "mp.im", "p.P.sk", "p.P.ut.1.3", "p.P.ut.1.4",
             "p.P.ut.1.5", "p.P.ut.1.7", "p.P.ut.1.8", "p.P.oe"}
    mp_states = ins.MediaPlayerStateIterator(log_entries, events_definition)
    fn_prefix = lambda st: "%4d " % st["frame_num"]
    parts = []
    for st in mp_states:
        if st["evname"] == "p.P.ut.1.9":
            if st["rescheduling_time"] < 0:
                parts.append("%4d !!! Scheduling in the past, reschedulling_time: %f" %
                             (st["frame_num"], st["rescheduling_time"]))
        elif st["evname"] in allow:
            parts.append(render_event(events_definition, st, fn_prefix))
    text = "\n".join(parts)
    return text


def rpt_counter(log_entries, events_definition=ins.mp_events):
    count_bads = ins.CountBads(events_definition, ins.mp_bads)
    counters = count_bads.count_bads(log_entries)
    text = format_anomalies_counter(count_bads.anomalies_description, counters)
    return text


def format_anomalies_counter(anomalies_description, counters, sample=None):
    parts = []
    fmt = "%4d %s"
    for anomaly in counters:
        if counters[anomaly]:
            desc = anomalies_description[anomaly]
            parts.append(fmt % (counters[anomaly], desc))
    if parts:
        parts_sorted = sorted(parts, key=lambda e: e[4:])
        text = "\n".join(parts_sorted)
        text = ("Counts of anomalies\n" +
                "qtty anomaly\n" + text)
    else:
        text = "No anomalies detected."
    if sample is not None:
        text = "Sample: %s\n" % sample + text
    return text


def fragment_crash_retries(pathserv):
    crashes_light_file = pathserv.special_raw_filename("crashes_light")
    if not os.path.isfile(crashes_light_file):
        text = "No crash info available, please run retry_crashes.py"
        return text
    total_retries, sometimes_crashed, still_crashing = fs.pickle_load(crashes_light_file)
    if len(sometimes_crashed) == 0:
        text = "No sample crashed the player."
        return text
    parts = []
    if still_crashing:
        parts.append("Samples that crashed in any one of the %d attempts to play" % (total_retries + 1))
        sorted_keys = sorted(still_crashing)
        for sample in sorted_keys:
            parts.append(sample)

    if still_crashing and sometimes_crashed:
        parts.append("")

    if sometimes_crashed:
        parts.append("Samples that crashed but finally played entirelly")
        finally_played = sometimes_crashed - still_crashing
        if finally_played:
            sorted_keys = sorted(finally_played)
            for sample in sorted_keys:
                parts.append(sample)
        else:
            parts.append("<none>")

    text = "\n".join(parts)
    return text


available_reports = {
    # <report name>: (<report function>, <Short description for user>)
    "anomalies": (rpt_anomalies, "Start, end and interesting events"),
    "all": (rpt_all, "All data is exposed as text"),
    "counter": (rpt_counter, "How many occurrences of each defect")
    }


def available_reports_description(line_prefix):
    d = available_reports
    lines = ["%s%s: %s" % (line_prefix, k, d[k][1]) for k in d]
    lines.sort()
    text = "\n".join(lines)
    return text


def report_by_name(name):
    try:
        fn_report = available_reports[name][0]
    except KeyError:
        raise mpexceptions.ExceptionUnknownReport(name)
    return fn_report


def report_session_comparison(session_comparison_data):
    sd = session_comparison_data
    header = "crashes | Defects per sample | session"
    fmt = "%7d | %18.3f | %s"
    parts = [header]

    cnt_crashes = len(sd.overall_counters.crashed_samples)
    score = sd.overall_counters.defects_per_sample()
    session = sd.overall_counters.pathserv.session
    parts.append(fmt % (cnt_crashes, score, session))

    cnt_crashes_o = len(sd.overall_counters.crashed_samples)
    score_o = sd.overall_counters_o.defects_per_sample()
    session_o = sd.overall_counters_o.pathserv.session
    parts.append(fmt % (cnt_crashes_o, score_o, session_o))

    parts.append("")
    c = sd.confidence_guess()
    parts.append("Confidence guess, from 1(highest) to 0(lowest): %.2f" % c)

    parts.append("")
    parts.append("Summary samples ignored for scores")
    parts.append("qtty | reason")
    # playlist
    n = len(sd.samples - sd.common_samples)
    parts.append("%4d   only on playlist session '%s'" % (n, session))
    n = len(sd.other_samples - sd.common_samples)
    parts.append("%4d   only on playlist session '%s'" % (n, session_o))
    # dbg
    n = len(sd.overall_counters.no_dbg_samples & sd.overall_counters_other.no_dbg_samples)
    parts.append("%4d   no .dbg in both sessions" % n)
    n = len(sd.overall_counters.no_dbg_samples - sd.overall_counters_other.no_dbg_samples)
    parts.append("%4d   .dbg missing only on session '%s'" % (n, session))
    n = len(sd.overall_counters_other.no_dbg_samples - sd.overall_counters.no_dbg_samples)
    parts.append("%4d   .dbg missing only on session '%s'" % (n, session_o))
    # crashes
    n = len(sd.overall_counters.crashed_samples & sd.overall_counters_other.crashed_samples)
    parts.append("%4d   crashed in both sessions" % n)
    n = len(sd.overall_counters.crashed_samples - sd.overall_counters_other.crashed_samples)
    parts.append("%4d   crashed only on session '%s'" % (n, session))
    n = len(sd.overall_counters_other.crashed_samples - sd.overall_counters.crashed_samples)
    parts.append("%4d   crashed only on session '%s'" % (n, session_o))

    text = "\n".join(parts)
    return text
