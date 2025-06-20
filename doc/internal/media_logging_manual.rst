Media logging manual
^^^^^^^^^^^^^^^^^^^^

Workflows
=========

User submitting debug info
--------------------------

Basically:

    - get samples
    - run a script
    - submit that directory

This is detailed in ``tools/ffmpeg/readme_run_tests.txt``.

Changing code in pyglet ffmpeg subsystem
----------------------------------------

Preparation like in readme_run_tests.txt, optionally install the library bokeh
(http://bokeh.pydata.org/en/latest/index.html) for visualization support.

The basic flow goes as:

- initialize the active session subsystem:
  set environment variable ``pyglet_mp_samples_dir`` to the desired
  samples_dir.
- record a session with the initial state::

    configure.py new <session> [playlist]
    run_test_suite.py

- Follow this workflow

  .. code-block:: none

      while True:
          edit code
          commit to hg
          record a new session:
              configure.py new <new session> [playlist]
              run_test_suite.py
          look at the last session reports in samples_dir/session/reports
          especially 00_summary.txt, which shows defects stats and list condensed
              info about any sample failing;
          then to look more details look at the individual reports.
          compare with prev sessions if desired:
              compare.py <session1> <session2>

          render additional reports:
              report.py sample

          or visualize the data collected with:
              bokeh_timeline.py sample

          if results are as wanted, break
      done, you may want to delete sessions for intermediate commits

It is possible to return to a previous session to request additional reports::

    configure.py activate <session>
    report.py ...

You can list the known sessions for the current samples_dir with::

    configure.py list

.. important::
    All this debugging machinery depends on a detailed and accurate capture of
    media_player related state, currently in examples/media_player.py and
    pyglet.media.player.

    Modifications in those modules may require matching modifications in
    pyglet/media/sources/instrumentation.py, and further propagation to other
    modules.


Changing the debug code for pyglet ffmpeg
-----------------------------------------

For initial debugging of debug code, where there are misspellings and trivial
errors to weed out, creating a new session for each run_test_suite.py run may
be inconvenient.

The flag ``dev_debug`` can be set to true in the session configuration file;
this will allow to rewrite the session.

Keep in mind that some raw data will be stale or misleading:

    - The ones captured at session creation time (currently pyglet.info and
      pyglet_changeset)
    - The collected crashes info (new crashes will not be seen)
    - If media_player.py crashes before doing any writing, the state recording
      will be the previous recording.

The reports using that stale raw data will obviously report stale data.

So it is a good idea to switch to a normal workflow as soon as possible
(simply creating a new session and deleting the special session).


Session
=======

If ``playlist_file`` is not specified, then all files in samples_dir, except
for the files with extension ".dbg", ".htm", ".html", ".json", ".log", ".pkl",
".py", ".txt" will make the implicit playlist; subdirectories of samples_dir
will **not** be explored.

If a ``playlist_file`` is specified, then it should contain one sample name
per line; a sanity check will be performed ensuring no blacklisted extension
is used, and that the sample exists in samples_dir.

Once the ``playlist_file`` is used in ``configure.py new`` a copy is written to
the session raw data directory, and this copy will be the authoritative
playlist for the session; ``playlist_file`` can be deleted if desired.

Specifying a playlist is useful in development to restrict the tests to
samples relevant to the feature or issue under work.

The session name will be used to create a samples_dir subdir to store the test
results, hence it should be different of previous sessions names, and it must
not contain slashes, ``/``, backslashes ``\`` or characters forbidden in
directory names.


Active session
==============

Most commands and subcommands target the currently active session.

A session becomes active when

    - a ``configure.py new session [playlist]`` is issued
    - a ``configure.py activate session`` is issued

The current implementation relies in two pieces of data to determine the
active session

    - the environment variable ``pyglet_mp_samples_dir`` specifies samples_dir,
      the directory where all the media samples reside. Under the current
      paths schema is also where session data will be stored, one subdir per
      session.

    - a file ``activation.json`` in samples_dir storing the name for the
      current active session.

Notice that the second precludes running two commands in parallel targeting
two different sessions in the same sample_dir.

The concept of active session plus the enforced path schema avoids the need to
provide paths at each command invocation, making for less errors, easier docs
and less typing.


Commands Summary
================

Primary commands
----------------

They are the ones normally used by developers

``configure.py``, ``mp.py`` : session creation, activation, protection, status
and list all.

``run_test_suite.py`` : plays session's samples, reports results.

``report.py`` : produces the specified report for the specified sample.

``timeline.py`` : translates the event stream to a stream of ``media_player``
state, useful to pass to other software.

``bokeh_timeline.py`` : visualization of data collected for the specified
sample.

Helper commands
---------------

Somehow an artifact of ``run_test_suite.py`` development, can help in testing
the debugging subsystem. ``run_test_suite.py`` is basically ``playmany.py +
retry_crashed.py + summarize.py``. When trying to change ``run_test_suite.py``
it is easier to first adapt the relevant helper.

``playmany.py`` : plays active session samples, recording media_player state
along the play.

``retry_crashed.py`` : plays again samples that have been seen always
crashing, hoping to get a recording with no crash. Motivated by early tests on
Ubuntu, where sometimes (but not always) a sample will crash the media_player.

``summarize.py`` : using the raw data produced by the two previous commands
elaborates some reports, aiming to give an idea of how well the run was and
what samples should be investigated.

Data directory layout
=====================

.. code-block:: none

    samples_dir/ : directory where the samples live, also used to store
                   sessions data
        <session name>/ : directory to store session info, one per session,
                          named as the session.
            dbg/ : recording of media_player events captured while playing a
                   sample, one per sample, named as sample.dbg; additional
                   versioning info, other raw data collected.
                _crashes_light.pkl : pickle with info for retry crashed
                _pyglet_hg_revision.txt
                _pyglet_info.txt
                _samples_version.txt
                _session_playlist.txt
                <one .dbg file per sample in the session playlist, named sample.dbg>
            reports/ : human readable reports rendered from the raw data (.txt),
                       visualizations (.html), intermediate data used by other
                       tools(.pkl)
            configuration.json : session configuration info, mostly permissions
        activation.json : holds the name of current active session
        <sample> : one for each sample

A subdirectory of samples_dir is detected as a session dir if:

    - it is a direct child of session dir
    - it has a ``configuration.json`` file

policies:

    - it should be hard to rewrite the .dbg files (recordings of media_player
      states)
    - think of dev analyzing data sent by an user.


Code Layout and conventions
===========================

The emerging separation of responsibilities goes like

Scripts (commands)
------------------

Structured as:

    - uses ``if __main__`` idiom to allow use as module (testing, sharing)
    - ``sysargs_to_mainargs()``: ``sys.argv`` translation to ``main`` params
    - ``main(...)``

        - params validation and translation to adequate code entities (uses
          module ``fs``).
        - translates exceptions to prints (uses module ``mpexceptions``)
        - short chain of instantiations / function calls to accomplish the
          command goals, no logic or calculations here.
    - other functions and classes: code specific to this command, delegates as
      much as possible to modules.

When two scripts use some related but not identical functionality, these parts
can be moved to another module. Example: at first ``summarize`` had the code to
collect defects stats, later, when ``compare`` was written, the module
``extractors`` was added and the defect collection stats code moved to that
module.

If script B needs a subset of unchanged script A functionality, it imports A
and uses what it needs. Example is ``retry_crashed``, will call into
``playmany``.

Because of the last point, some scripts will also be listed as modules.


Modules
-------


buffered_logger
_______________

Accumulation of debug events while playing media_player, saves when
sample's play ends


instrumentation
_______________

Defines the events that modify media_player state.
Defines which events are potential defects.
Gives the low level support to extract info from the recorded data.

For new code here, keep accepting and returning only data structures, no paths
or files.


fs
__

Path building for entities into a session directory should be delegated to
``fs.PathServices``.
Session's creation, activation and management at start of ``fs``.
Versions capture are handled at start of module ``fs``.
Utility functions to load - save at the end of ``fs``.

While there isn't a ``Session`` object, in practice the code identifies and
provides access to a particular session data by handling a ``fs.PathServices``
instance.


extractors
__________

Analyzes a media_player recording to build specific info on behalf of
reporters. Uses ``instrumentation`` to get input data about the media_player
state sequence seen while playing a sample.
Defines object types to collect some specific info about a replay.


reports
_______

Formats as text info captured / generated elsewhere.


mpexceptions
____________

Defines exceptions generated by code in the ffmpeg debug subsystem.


Scripts that also acts as modules
---------------------------------

timeline
________

Renders the media player's debug info to a format more suitable to postprocess
in a spreadsheets or other software, particularly to get a data visualization.
(used by ``bokeh_timeline.py``)

playmany
________

Produces media_player debug recordings.
Runs python scripts as subprocesses with a timeout (used by retry_crashed.py).


Commands detailed
=================

bokeh_timeline.py
-----------------

Usage::

    bokeh_timeline.py sample

Renders media player's internal state graphically using bokeh.

Arguments:

.. code-block:: none

    sample: sample to report

The output will be written to session's output dir under
``reports/sample.timeline.html``.

Notice the plot can be zoomed live with the mouse wheel, but you must click
the button that looks as a distorted **OP**; it also does pan with mouse drag.

Example::

    bokeh_timeline.py small.mp4

will write the output to ``report/small.mp4.timeline.html``.


compare.py
----------

Usage::

    compare.py --reldir=relpath other_session

Builds a reports comparing the active session with other_session.

Outputs to ``samples_dir/relpath/comparison_<session>_<other_session>.txt``.


configure.py
------------

Usage::

    configure.py subcommand [args]

Subcommands:

.. code-block:: none

    new session [playlist] : Creates a new session, sets it as the active one
    activate session : activates a session
    deactivate : no session will be active
    protect [target]: forbids overwrite of session data
    status : prints configuration for the active session
    help [subcommand] : prints help for the given subcommand or topic
    list : list all sessions associated the current samples_dir

Creates and manages pyglet media_player debug session configurations.

Most commands and subcommands need an environment variable
``pyglet_mp_samples_dir`` to be set to the directory where the media samples
reside.

The configuration stores some values used when other commands are executed,
mostly protection status.

This command can be called both as ``configure.py`` or ``mp.py``, they do the
same.


mp.py
-----

alias for ``configure.py``


playmany.py
-----------

Usage::

    playmany.py

Uses media_player to play a sequence of samples and record debug info.

A session must be active, see command ``configure.py``
If the active configuration has disallowed dbg overwrites it will do nothing.

If a playlist was provided at session creation, then only the samples in the
playlist will be played, otherwise all files in ``samples_dir``.


report.py
---------

Usage::

    report.py sample report_name

Generates a report from the debugging info recorded while playing sample.

Arguments:

.. code-block:: none

    sample: sample to report
    report_name: desired report, one of
        "anomalies": Start, end and interesting events
        "all": All data is exposed as text
        "counter": How many occurrences of each defect

The report will be written to session's output dir under
``reports/sample.report_name.txt``.

Example::

    report anomalies small.mp4

will write the report *anomalies* to ``report/small.mp4.anomalies.txt``.

The authoritative list of reports available comes from
``reports.available_reports``


retry_crashed.py
----------------

Usage::

    retry_crashed.py [--clean] [max_retries]

Inspects the raw data collected to get the list of samples that crashed the
last time they were played.
Then it replays those samples, recording new raw data for them.

The process is repeated until all samples has a recording with no crashes or
the still crashing samples were played ``max_tries`` times in this command
run.

Notice that only samples recorded as crashing in the last run are retried.

A configuration must be active, see command ``configure.py``.

Besides the updated debug recordings, a state is build and saved:

.. code-block:: none

    total_retries: total retries attempted, including previous runs
    sometimes_crashed: list of samples that crashed one time but later
                       completed a play
    always_crashed: list of samples that always crashed

Options:

.. code-block:: none

    --clean: discards crash data collected in a previous run
    max_retries: defaults to 5


run_test_suite.py
-----------------

Usage::

    run_test_suite.py [samples_dir]

Plays media samples with the pyglet media_player, recording debug information
for each sample played and writing reports about the data captured.

Arguments:

.. code-block:: none

    samples_dir: directory with the media samples to play

If no samples_dir is provided the active session is the target.
If an explicit playlist was specified when creating the session, then only the
samples in the playlist will be played, otherwise all samples in samples_dir
will be played.

If sample_dir is provided, a session named ``testrun_00`` (``_01``, ``_02``,
... if that name was taken) will be created, with no explicit playlist, and
then the command operates as in the previous case.

Output files will be into:

.. code-block:: none

    samples_dir/session/dbg : binary capture of media_player events, other raw
                              data captured
    samples_dir/session/reports : human readable reports

.. note::

    This script will refuse to overwrite an existing ``test_run results``.

Output files will be into subdirectories:

``samples_dir/test_run/dbg``

    Each sample will generate a ``sample.dbg`` file storing the sequence of
    player debug events seen while playing the sample.
    It is simply a pickle of a list of tuples, each tuple an event.
    There are not meant for direct human use, but to run some analyzers to
    render useful reports.

    A ``crash_retries.pkl`` file, a pickle of
    ``(total_retries, sometimes_crashed, still_crashing) <-> (int, set, set)``.

    A ``pyglet.info`` captured at session creation to track hw & sw.

    A pyglet hg revision captured at session creation.

``samples_dir/test_run/reports``

    Human readable outputs, described in command ``summarize.py``

    Later a user can generate visualizations and additional reports that will
    be stored in this directory


summarize.py
------------

Usage::

    summarize.py

Summarizes the session info collected with ``playmany`` and ``retry_crashes``.

A configuration must be active, see command ``configure.py``.

If a playlist was provided at session creation, then only the samples in the
playlist will be played, otherwise all files in samples_dir.

Produces human readable reports, constructed from the .dbg files.

Output will be in

    ``samples_dir/test_run/reports``

The files in that directory will be

``00_summary.txt`` , which provides:

    - basics defects stats over all samples
    - a paragraph for each non perfect sample play with the count of each
      anomaly observed

``03_pyglet_info.txt`` , ``pyglet.info`` output giving OS, python version,
etc (as captured at session creation).

``04_pyglet_hg_revision.txt`` , pyglet hg revision if running from a repo
clone, non written if no repo (as captured at session creation).

``sample_name.all.txt`` and ``sample_name.anomalies.txt`` for each sample that
played non perfect.

``sample_name.all.txt`` has all info in the ``sample_name.dbg`` in human
readable form, that is, the sequence of player's internal events along the
play.

``sample_name.anomalies.txt`` is a reduced version of the ``.all``.
variant: normal events are not shown, only anomalies.


timeline.py
-----------

Usage::

    timeline.py sample [output_format]

Renders the media player's debug info to a format more suitable to postprocess
in a spreadsheets or other software, particularly to get a data visualization.

See output details in the manual.

Arguments:

.. code-block:: none

    sample: sample to report
    output_format : one of { "csv", "pkl"}, by default saves as .pkl (pickle)

The output will be written to session's output dir under
``reports/sample.timeline.[.pkl or .csv]``.

Example::

    timeline.py small.mp4

will write the output to ``report/small.mp4.timeline.pkl``.

.. note::
    ``.csv`` sample is currently not implemented.


Samples
=======

Samples should be small, at the moment I suggest an arbitrary 2MB 2 minutes
limit. The samples dir contains a ``_sources.txt`` which lists from where
each sample comes.

Caveat:

    Samples are not 'certified to be compliant with the specification'.

    When possible, samples should be played with non ffmpeg software for
    incidental confirmation of well formed

        ``*.mp4``, ``*.3gp`` played well with Windows Media Player for win7

        ``*.ogv``, ``*. webm`` played well with Firefox 54.0

        ``*.flv``, ``*.mkv`` played well with VLC Media player, but VLC uses
        ffmpeg

Surely the samples set will be refined as time goes.


pycharm notes
=============

For ``examples/video_ffmpeg`` module visibility and code completion, that
directory should be a 'content root' in pycharm settings | 'project
structure'; as projects roots cannot nest, the pyglet working copy cannot be a
'content root', I removed it; I added also working_copy/pyglet as another
'content root' so pycharm plays well also en the library proper. This with
pycharm 2017.2
