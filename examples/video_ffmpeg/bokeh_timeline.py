"""
Usage

    bokeh_timeline.py sample

Renders media player's internal state graphically using bokeh

Arguments
    sample: sample to report

The output will be written to session's output dir under
    reports/sample.timeline.html

Notice the plot can be zoomed live with the mouse wheel, but you must click
the button that looks as a distorted 'OP'; it also does pan with mouse drag.

Example

    bokeh_timeline.py small.mp4

will write the output to report/small.mp4.timeline.html
"""
# just in case, this version was developed and tested with bokeh vs 0.12.6 (win)

import os
import sys

from bokeh.layouts import column
from bokeh.models import LinearAxis, Range1d
from bokeh.plotting import figure, output_file, show

import fs
import mpexceptions
import timeline


def main(sample):
    try:
        pathserv = fs.get_path_info_for_active_session()
    except mpexceptions.ExceptionUndefinedSamplesDir:
        print("The env var 'pyglet_mp_samples_dir' is not defined.")
        return 1
    except mpexceptions.ExceptionNoSessionIsActive:
        print("*** Error, no session active.")
        return 1

    bokeh_render_timeline(pathserv, sample)


def bokeh_render_timeline(pathserv, sample):
    infile = pathserv.report_filename(sample, "timeline.pkl", False)
    if not os.path.isfile(infile):
        timeline.save_timeline(pathserv, sample, ".pkl")

    timeline_postprocessed = fs.pickle_load(infile)
    info = unpack_timeline(timeline_postprocessed)
    outfile = pathserv.report_filename(sample, "timeline.html", False)
    make_plot(info, outfile)


def unpack_timeline(timeline_postprocessed):
    timeline, current_time_nones, audio_time_nones = timeline_postprocessed
    (wall_times, pyglet_times, audio_times, current_times,
     frame_nums, rescheds) = zip(*timeline)

    if current_time_nones:
        x_vnones, y_vnones = zip(*current_time_nones)
    else:
        x_vnones, y_vnones = [], []

    if audio_time_nones:
        x_anones, y_anones = zip(*audio_time_nones)
    else:
        x_anones, y_anones = [], []

    return (wall_times, pyglet_times, audio_times,
            current_times, frame_nums, rescheds,
            x_vnones, y_vnones,
            x_anones, y_anones)


def make_plot(info, outfile):
    # prepare some data
    (wall_times, pyglet_times, audio_times,
     current_times, frame_nums, rescheds,
     x_vnones, y_vnones,
     x_anones, y_anones) = info

    # output to static HTML file
    output_file(outfile)

    # main plot
    p = figure(
       tools="pan,wheel_zoom,reset,save",
       y_axis_type="linear", y_range=[0.000, wall_times[-1]], title="timeline",
       x_axis_label='wall_time', y_axis_label='time',
       plot_width=600, plot_height=600
    )

    # add some renderers
    p.line(wall_times, wall_times, legend="wall_time")
    #p.line(wall_times, pyglet_times, legend="pyglet_time", line_width=3)
    p.line(wall_times, current_times, legend="current_times", line_color="red")
    p.line(wall_times, audio_times, legend="audio_times", line_color="orange", line_dash="4 4")

    p.circle(x_vnones, y_vnones, legend="current time nones", fill_color="green", size=8)
    p.circle(x_anones, y_anones, legend="audio time nones", fill_color="red", size=6)

    # secondary y-axis for frame_num
    p.extra_y_ranges = {"frame_num": Range1d(start=0, end=frame_nums[-1])}
    p.line(wall_times, frame_nums, legend="frame_num",
           line_color="black", y_range_name="frame_num")
    p.add_layout(LinearAxis(y_range_name="frame_num", axis_label="frame num"), 'left')

    p.legend.location = "bottom_right"
    # show the results
    #show(p)

    # secondary plot for rescheduling times
    q = figure(
       tools="pan,wheel_zoom,reset,save",
       y_axis_type="linear", y_range=[-0.3, 0.3], title="rescheduling time",
       x_axis_label='wall_time', y_axis_label='rescheduling time',
       plot_width=600, plot_height=150
    )
    q.line(wall_times, rescheds)

    show(column(p, q))


def usage():
    print(__doc__)
    sys.exit(1)


def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) < 2:
        usage()
    sample = sys.argv[1]
    return sample


if __name__ == '__main__':
    sample = sysargs_to_mainargs()
    main(sample)
