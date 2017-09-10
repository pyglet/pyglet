"""configure.py script to get / set some session configurable values; mp.py is
an alias for this command.
"""

import sys

import fs
import mpexceptions


template_cmd = (
"""
Usage

    &cmd subcommand [args]

Subcommands

    new session [playlist] : Creates a new session, sets it as the active one
    activate session : activates a session 
    deactivate : no session will be active
    protect [target]: forbids overwrite of session data
    status : prints configuration for the active session
    help [subcommand] : prints help for the given subcommand or topic
    list : list all sessions associated the current samples_dir 

Creates and manages pyglet media_player debug session configurations.

Most commands and subcommands need an environment variable pyglet_mp_samples_dir
to be set to the directory where the media samples reside.

The configuration stores some values used when other commands are executed.

    samples_dir: directory where the samples reside
    session: a name to identify a particular session
    session_dir: directory to store all the session's output files, set to  
                 samples_dir/session
    permissions to overwrite or not raw data collected or generated reports
    playlist: subset of samples to play

This command can be called both as 'configure.py' or 'mp.py', they do the same.

"""
)

template_subcommands = (
"""
new
Usage

    &cmd new session [playlist_file]

Arguments

    session       : a name to identify this particular session
    playlist_file : file with a list of samples

Creates a new session and a directory to save session outputs.

The configuration is saved to disk and the session is made the active one.

If playlist_file os specified, only the samples in the playlist will be
considered as targets for a general command. 

General commands will use the configuration of the active session to know from
where to read and write data.

@
activate
Usage

    &cmd activate session

Arguments

    session: name of session to activate.

Sets the session as the active one.

General commands will use the configuration of the active session to know from
where to read and write data.

@
deactivate
Usage

    &cmd deactivate

Makes the current session inactive.

No session will be active, so general commands will not modify any session data.

Mostly as a precaution so that a slip in shell history does not overwrite
anything.
@
protect
Usage

    &cmd protect target

Arguments

target: one of

"raw_data"
    Forbids general commands to overwrite session's raw data captured.
    Helps to not mix in the same session results obtained in different conditions.

"reports"
    Forbids general commands to overwrite session's generated reports.
    Useful if the reports are manually annotated.

@
status
Usage

    &cmd status [session]

Arguments

    session: name of session

Prints the configuration for the active session.

@
help
Usage

    &cmd help [subcommand or topic]

Subcommands

    new session [playlist] : Creates a new session, sets it as the active one
    activate session : activates a session 
    deactivate : no session will be active
    protect [target]: forbids overwrite of session data
    status : prints configuration for the active session
    help [subcommand] : prints help for the given subcommand or topic
    list : list all sessions associated the current samples_dir 

Topics

    layout  : data layout on disk
    session : sessions what and whys
    workflow: common workflows
    gencmds : general commands
@
list
Usage

    &cmd list

List all sessions associated with the current sample_dir


"""
)


def sub_and_template_from_section(s):
    subcommand, template = s[1:].split("\n", 1)
    return subcommand, template


def help_texts_from_template(cmd):
    cmd_help = template_cmd.replace("&cmd", cmd)

    all_subcommands = template_subcommands.replace("&cmd", cmd)
    parts = all_subcommands.split("@")
    pairs = [sub_and_template_from_section(s) for s in parts]
    subcommands_help = {a: b for a, b in pairs}

    return cmd_help, subcommands_help


def test_help_strings():
    cmd_help, subcommands_help = help_texts_from_template('mp')
    print(cmd_help)
    for e in subcommands_help:
        print("sub:", repr(e))
        print("|%s|" % subcommands_help[e])


def show_configuration(keys_to_show=None):
    pathserv = fs.get_path_info_for_active_session()
    conf = fs.json_load(pathserv.configuration_filename())
    if keys_to_show is None:
        keys_to_show = conf.keys()
    print("session:", pathserv.session)
    for k in sorted(keys_to_show):
        print("\t%s: %s" % (k, conf[k]))


def sub_activate():
    if len(sys.argv) < 3:
        print("*** Error, missing argument.\n")
        print(subcommands_help["activate"])
        return 1
    session = sys.argv[2]
    fs.activation_set_to(session)
    return 0


def sub_deactivate():
    session = None
    fs.activation_set_to(session)
    return 0


def sub_help():
    if len(sys.argv) < 3:
        topic = "help"
    else:
        topic = sys.argv[2]
    print(subcommands_help[topic])
    return 0


def sub_list():
    samples_dir = fs.get_current_samples_dir()
    sessions = fs.get_sessions(samples_dir)
    for session in sorted(sessions):
        print(session)
    return 0


def sub_new():
    if len(sys.argv) < 3:
        print("*** Error, missing argument.\n")
        print(subcommands_help["new"])
        return 1

    session = sys.argv[2]
    if len(sys.argv) > 3:
        playlist_file = sys.argv[3]
    else:
        playlist_file = None
    fs.new_session(session, playlist_file)
    return 0


def sub_protect():
    if len(sys.argv) < 3:
        print("*** Error, missing argument.\n")
        print(subcommands_help["protect"])
        return 1

    name = sys.argv[2]
    if name not in {"raw_data", "reports"}:
        print("*** Error, unknown name to protect. name:", name)
        print(subcommands_help["protect"])
        return 1
    modify = {("protect_" + name): True}
    fs.update_active_configuration(modify)
    return 0


def sub_status():
    show_configuration()
    return 0


def dispatch_subcommand(caller):
    global cmd_help, subcommands_help
    cmd_help, subcommands_help = help_texts_from_template(caller)
    if len(sys.argv) < 2:
        sub = "help"
    else:
        sub = sys.argv[1]
    try:
        returncode = globals()["sub_" + sub]()
    except KeyError:
        print("*** Error, unknown subcommand:", sub)
        returncode = 1
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined")
        returncode = 1
    except mpexceptions.ExceptionSamplesDirDoesNotExist as ex:
        print("The env var 'pyglet_mp_samples_dir' does not point to an existing directory")
        returncode = 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session is active.")
        returncode = 1
    except mpexceptions.ExceptionNoSessionWithThatName:
        print("*** Error, no session by that name")
        returncode = 1
    except mpexceptions.ExceptionSessionExistWithSameName:
        print("*** Error, session exists")
        returncode = 1
    except mpexceptions.ExceptionPlaylistFileDoNotExists:
        print("*** Error, playlist_file does not exist")
        returncode = 1
    except mpexceptions.ExceptionBadSampleInPlaylist as ex:
        print("*** Error, bad sample(s) name in playlist (bad extension or non-existent):")
        for sample in ex.rejected:
            print("\t%s" % sample)
        returncode = 1

    sys.exit(returncode)

if __name__ == "__main__":
    dispatch_subcommand("configure.py")
