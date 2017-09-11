"""
Responsabilities

Path building for entities into a session should be delegated to fs.PathServices
Session's creation, activation and management at start of fs
Versions capture are handled at start of module fs
Utility functions to load - save at the end of fs

See directory layout in manual.
"""
import sys
import json
import os
import pickle
import shutil
import subprocess

import mpexceptions

def get_media_player_path():
    here = os.path.basename(os.path.abspath(__file__))
    path = os.path.join("..", "..", "examples", "video_ffmpeg")
    mp_path = os.path.abspath(path)
    return mp_path

# available sessions, activation related functionality #######################


def activation_set_to(session):
    """
    exceptions:
        mpexceptions.ExceptionUndefinedSamplesDir
        mpexceptions.ExceptionNoSessionWithThatName
        mpexceptions.ExceptionSamplesDirDoesNotExist
    """
    samples_dir = get_current_samples_dir()
    activation_file = get_activation_filename(samples_dir)
    if session is None:
        if os.path.isfile(activation_file):
            os.remove(activation_file)
    else:
        json_save(session, activation_file)


def get_current_samples_dir():
    if "pyglet_mp_samples_dir" not in os.environ:
        raise mpexceptions.ExceptionUndefinedSamplesDir()
    path = os.environ["pyglet_mp_samples_dir"]
    if not os.path.isdir(path):
        raise mpexceptions.ExceptionSamplesDirDoesNotExist(path)
    return path


def get_path_info_for_active_session():
    samples_dir = get_current_samples_dir()
    activation_file = get_activation_filename(samples_dir)
    try:
        session = json_load(activation_file)
    except FileNotFoundError:
        raise mpexceptions.ExceptionNoSessionIsActive()
    pathserv = PathServices(samples_dir, session)
    return pathserv


def get_path_info_for_session(session):
    """
    samples_dir comes from env var pyglet_mp_samples_dir
    """
    samples_dir = get_current_samples_dir()
    pathserv = PathServices(samples_dir, session)
    conf_file = pathserv.configuration_filename()
    if os.path.isdir(pathserv.session_dir) and os.path.isfile(conf_file):
        return pathserv
    raise mpexceptions.ExceptionNoSessionWithThatName()


def get_sessions(samples_dir):
    candidates = [s for s in os.listdir(samples_dir)
                  if os.path.isdir(os.path.join(samples_dir, s))]
    sessions = []
    for name in candidates:
        pathserv = PathServices(samples_dir, name)
        if os.path.isfile(pathserv.configuration_filename()):
            sessions.append(name)
    return sessions


def get_activation_filename(samples_dir):
    return os.path.join(samples_dir, "activation.json")


def new_session(session, playlist_file=None):
    """creates a new session and sets as the active session"""
    samples_dir = get_current_samples_dir()
    new_session_for_samples_dir(session, samples_dir, playlist_file)
    activation_set_to(session)


def new_session_for_samples_dir(session, samples_dir, playlist_file=None):
    """creates a new session and returns it's pathserv, session is not activated

    Does not use env vars.
    """
    if not os.path.isdir(samples_dir):
        raise mpexceptions.ExceptionSamplesDirDoesNotExist(samples_dir)
    pathserv = PathServices(samples_dir, session)
    if os.path.exists(pathserv.session_dir):
        raise mpexceptions.ExceptionSessionExistWithSameName()
    conf = default_initial_configuration()

    if playlist_file is not None:
        if not os.path.isfile(playlist_file):
            raise mpexceptions.ExceptionPlaylistFileDoNotExists()
        conf["has_playlist"] = True
        samples = sane_samples_from_playlist(pathserv, playlist_file)
    else:
        samples = [sample for sample, fname in pathserv.playlist_generator_all()]

    # directory creation delayed to last possible moment so exceptions don't
    # left empty session dir
    for path in pathserv.dirs_to_create():
        os.mkdir(path)

    dump_pyglet_info(pathserv)
    copy_samples_version_to_dbg(pathserv)
    save_session_playlist(pathserv, samples)
    json_save(conf, pathserv.configuration_filename())
    dump_hg_changeset(pathserv)
    return pathserv


def dump_pyglet_info(pathserv):
    import pyglet
    import pyglet.info
    filename = pathserv.special_raw_filename("pyglet_info")
    old = sys.stdout
    try:
        with open(filename, "w", encoding="utf-8") as f:
            sys.stdout = f
            pyglet.info.dump()
    except Exception as ex:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = old


# assumes the cwd hits into pyglet clone under test
def dump_hg_changeset(pathserv):
    fname = pathserv.special_raw_filename("pyglet_hg_revision")
    # win needs shell=True to locate the 'hg'
    shell = (sys.platform == "win32")
    with open(fname, "w", encoding="utf8") as outfile:
        subprocess.call(["hg", "parents", "--encoding", "utf8"],
                    shell=shell,
                    stdout=outfile,
                    timeout=5.0)


def copy_samples_version_to_dbg(pathserv):
    src = pathserv.samples_version_filename()
    dst = pathserv.special_raw_filename("samples_version")
    shutil.copyfile(src, dst)


def sane_samples_from_playlist(pathserv, playlist_file):
    # files exist and extension is not blacklisted
    samples = []
    rejected = []
    for sample, filename in pathserv.playlist_generator_from_file(playlist_file):
        ext = os.path.splitext(sample)[1]
        if (ext in {".dbg", ".htm", ".html", ".json",
                    ".log", ".pkl", ".py", ".txt"} or
            not os.path.isfile(filename)):
            rejected.append(sample)
        else:
            samples.append(sample)
    if len(rejected) > 0:
        raise mpexceptions.ExceptionBadSampleInPlaylist(rejected)
    return samples


def save_session_playlist(pathserv, samples):
    outfile = pathserv.special_raw_filename("session_playlist")
    text = "\n".join(sorted(samples))
    txt_save(text, outfile)


def load_session_playlist(pathserv):
    infile = pathserv.special_raw_filename("session_playlist")
    text = txt_load(infile)
    lines = text.split("\n")
    samples = [s.strip() for s in lines]
    return samples


# session configuration functionality #########################################


def default_initial_configuration():
    conf = {
        "config_vs": "1.0",
        "protect_raw_data": False,
        "protect_reports": False,
        "dev_debug": False,
        "has_playlist": False,
        }
    return conf


def update_active_configuration(modify):
    """updates the active session configuration file with the key: values in modify"""
    pathserv = get_path_info_for_active_session()
    update_configuration(pathserv, modify)


# validation over modify keys and values is a caller responsibility,
# here only verified that if key in modify then key in conf
def update_configuration(pathserv, modify):
    """The session associated with pathserv gets it's configuration updated
    with the key: values in modify"""
    conf = json_load(pathserv.configuration_filename())
    for k in modify:
        assert k in conf
    conf.update(modify)
    json_save(conf, pathserv.configuration_filename())


def get_session_configuration(pathserv):
    conf = json_load(pathserv.configuration_filename())
    return conf


# path functionality according to path schema ##################################


class PathServices(object):
    def __init__(self, samples_dir, session):
        self.samples_dir = samples_dir
        self.session = session
        self.session_dir = os.path.join(samples_dir, session)

        self.dbg_dir = os.path.join(self.session_dir, "dbg")
        self.rpt_dir = os.path.join(self.session_dir, "reports")

    def dirs_to_create(self):
        return [self.session_dir, self.dbg_dir, self.rpt_dir]

    def sample(self, filename):
        """returns sample name from filename

        dev note: no checks performed, maybe it should check
           - filename point into the sample_dir directory
           - filename exists
        """
        return os.path.basename(filename)

    def filename(self, sample):
        """Returns the filename for the sample

        dev note: no checks performed, maybe it should check
           - filename exists
        """
        return os.path.join(self.samples_dir, sample)

    def dbg_filename(self, sample):
        """Returns filename to store media_player's internal state recording for sample"""
        return os.path.join(self.dbg_dir, sample + ".dbg")

    def sample_from_dbg_filename(self, filename):
        return os.path.splitext(filename)[0]

    def samples_version_filename(self):
        return os.path.join(self.samples_dir, "_version.txt")

    def report_filename(self, sample, report_name, txt=True):
        """Returns filename to store a 'per sample' report for sample"""
        if txt:
            s = os.path.join(self.rpt_dir, "%s.%s.txt" % (sample, report_name))
        else:
            s = os.path.join(self.rpt_dir, "%s.%s" % (sample, report_name))
        return s

    def special_report_filename(self, report_name):
        """Returns filename to store a report that don't depend on a single sample"""
        table = {
            # report_name: shortname
            "summary": "00_summary.txt",
            "pyglet_info": "00_pyglet_info.txt",
            "pyglet_hg_revision": "04_pyglet_hg_revision.txt"
            }
        return os.path.join(self.rpt_dir, table[report_name])

    def special_raw_filename(self, shortname):
        table = {
            "session_playlist": "_session_playlist.txt",
            "crashes_light": "_crashes_light.pkl",
            "pyglet_info": "_pyglet_info.txt",
            "samples_version": "_samples_version.txt",
            "pyglet_hg_revision": "_pyglet_hg_revision.txt"
            }
        return os.path.join(self.dbg_dir, table[shortname])

    def configuration_filename(self):
        return os.path.join(self.session_dir, "configuration.json")

    def playlist_generator(self, playlist_text):
        lines = playlist_text.split("\n")
        for line in lines:
            sample = line.strip()
            if sample == "" or sample.startswith("#"):
                continue
            yield (sample, self.filename(sample))

    def playlist_generator_from_file(self, playlist_file):
        with open(playlist_file, "r", encoding="utf-8") as f:
            text = f.read()
        gen = self.playlist_generator(text)
        yield from gen

    def playlist_generator_all(self):
        for name in os.listdir(self.samples_dir):
            filename = os.path.join(self.samples_dir, name)
            ext = os.path.splitext(name)[1]
            if (ext in {".dbg", ".htm", ".html", ".json",
                        ".log", ".pkl", ".py", ".txt"} or
                os.path.isdir(filename)):
                continue
            yield (name, filename)

    def playlist_generator_from_samples_iterable(self, samples):
        for sample in samples:
            yield (sample, self.filename(sample))

    def playlist_generator_from_fixed_text(self):
        text = "0\n1\n2\n3\n4\n5\n6\n7\n8\n9\nz"
        gen = self.playlist_generator(text)
        yield from gen

    def session_playlist_generator(self):
        playlist_file = self.special_raw_filename("session_playlist")
        gen = self.playlist_generator_from_file(playlist_file)
        yield from gen

    def session_exists(self):
        filename = self.configuration_filename()
        return os.path.isdir(self.session_dir) and os.path.isfile(filename)


# fs io #######################################################################


def json_save(obj, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def json_load(filename):
    with open(filename, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return obj


def pickle_save(obj, filename):
    with open(filename, "wb") as f:
        pickle.dump(obj, f)


def pickle_load(filename):
    with open(filename, "rb") as f:
        obj = pickle.load(f)
    return obj


def txt_load(filename):
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
    return text


def txt_save(text, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def test_composition():
    text = "0\n1\n2\n3\n4\n5\n6\n7\n8\n9\nz"
    # samples_dir, session
    args = "aaa", "bbb"
    a = PathServices(*args)
    for u, v in zip(a.playlist_generator(text), a.playlist_generator_from_fixed_text()):
        print(u, v)

#test_composition()
