"""
Responsabilities

Containers with helper functions to analyze media_player recording(s)

Commands 'compare' and 'summarize' uses them to build its reports.

"""

import os

import fs


class OverallDefectsCounter:
    """Helper class to count defects over a range of media player sample plays

    Collaborates with a caller, which determines which samples to process and
    which samples to skip.

    The main result is a dict of defect: count over all suitable samples

    Additionally, classifies the samples in the disjoint sets:
        crashed_samples: samples that crashed
        no_dbg_samples: samples with no media_player state recording
        skipped_samples: samples that the caller excludes from the overall counts
        perfect_play_samples: non-skipped samples that played perfectly
        counters_non_perfect_play_samples: A dict of
            sample: <counters for each defect type found in recording>
            for each sample with dbg, no crash, no perfect, not skipped.

    The overall defect counters only uses the samples in the last group.

    Used to:
        - calculate a session quality score (crashes, defects per sample)
        - decide which of two session behaves better

    Notice that the more samples are discarded, the less significant will be
    the score; a good report will need to consider that.

    design notes
        - this is a bit overcomplicated for single session score, but
          probably the minimum while comparing two sessions.
    """

    def __init__(self, pathserv, fn_count_bads):
        self.pathserv = pathserv
        self.fn_count_bads = fn_count_bads
        self.crashed_samples = set()
        self.no_dbg_samples = set()
        self.perfect_play_samples = set()
        self.counters_non_perfect_play_samples = {}
        self.skipped_samples = set()
        self.overall_counters = dict()
        self.overall_counters["scheduling_in_past"] = 0
        self.last_count = None

    def count_defects(self, sample):
        dbg_file = self.pathserv.dbg_filename(sample)
        if not os.path.isfile(dbg_file):
            self.no_dbg_samples.add(sample)
            classifies_as = "no_dbg"
            counters = None
        else:
            log_entries = fs.pickle_load(dbg_file)
            counters = self.fn_count_bads(log_entries)
            if counters["crash"]:
                self.crashed_samples.add(sample)
                classifies_as = "crash"
            else:
                perfect = all((counters[k] == 0 for k in counters))
                classifies_as = "perfect" if perfect else "non_perfect"
        self.last_count = sample, classifies_as, counters
        return classifies_as

    def add_count(self, skip=False):
        sample, classifies_as, counters = self.last_count
        self.last_count = None
        if classifies_as in {"no_dbg", "crash"}:
            return
        if skip:
            self.skipped_samples.add(sample)
            return
        if classifies_as == "perfect":
            self.perfect_play_samples.add(sample)
        else:
            self.counters_non_perfect_play_samples[sample] = counters
            for k in counters:
                self.overall_counters[k] = self.overall_counters.get(k, 0) + counters[k]

    def sum_overall(self):
        total = 0
        for k in self.overall_counters:
            total += self.overall_counters[k]
        return total

    def total_relevant_samples(self):
        total = (len(self.perfect_play_samples) +
                 len(self.counters_non_perfect_play_samples))
        return total

    def defects_per_sample(self):
        return self.sum_overall() / self.total_relevant_samples()


def single_session_overall_defect_counters(pathserv, fn_count_bads):
    overall = OverallDefectsCounter(pathserv, fn_count_bads)
    samples = {e[0] for e in pathserv.session_playlist_generator()}
    for sample in samples:
        overall.count_defects(sample)
        overall.add_count()
    return overall


class CollectSessionComparisonData:
    """Collects data to compare two sessions

    Constructs the sets samples, other_samples, common_samples, no_dbg_samples,
    crashed_samples, compared_samples

    For each session calculates an OverallDefectsCounter instance over the set
    compared_samples; results stored in overall_counters and
    overall_counters_other.
    """
    def __init__(self, pathserv, pathserv_other, fn_count_bads):
        self.pathserv = pathserv
        self.pathserv_other = pathserv_other

        # intersection playlist
        samples = {e for e in fs.load_session_playlist(pathserv)}
        other_samples = {e for e in fs.load_session_playlist(pathserv_other)}
        common_samples = samples & other_samples

        # count defects, only for samples with no crash in both sessions
        no_dbg_samples = set()
        crashed_samples = set()
        compared_samples = set()
        cls = OverallDefectsCounter
        overall_counters = cls(pathserv, fn_count_bads)
        overall_counters_o = cls(pathserv_other, fn_count_bads)
        for sample in common_samples:
            perfect, counters = overall_counters.count_defects(sample)
            perfect_o, counters_o = overall_counters_o.count_defects(sample)
            if counters["no_dbg"] or counters_o["no_dbg"]:
                no_dbg_samples.add(sample)
                continue
            if counters["crash"] or counters_o["crash"]:
                crashed_samples.add(sample)
                continue
            compared_samples.add(sample)
            overall_counters.count_defects(sample)
            overall_counters_o.count_defects(sample)

        self.no_dbg_samples = no_dbg_samples
        self.samples = samples
        self.other_samples = other_samples
        self.common_samples = common_samples
        self.crashed_samples = crashed_samples
        self.compared_samples = compared_samples
        self.overall_counters = overall_counters
        self.overall_counters_other = overall_counters_o

    def confidence_guess(self):
        """estimates how meaningful the defects per sample are

        The value will be between 1(most meaningful) and 0(useless).

        It follows the heuristic 'the more samples are discarded, the less
        meaning will be the conclusions draw'
        """
        maxz = max(len(self.samples), len(self.other_samples))
        c = len(self.compared_samples) / maxz if maxz > 0 else 0
        return c
