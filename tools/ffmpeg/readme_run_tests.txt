Running the tests
=================

preparation
-----------

1. You need to have ffmpeg binaries to get the dynamic link libraries, 
Windows:
Download the binaries from http://ffmpeg.zeranoe.com/builds/ ; that page lets select Version / Architecture / Linking
We need to select
	'shared' to get the dll's
	'Architecture' according to the target machine (32/64bits)
	'Version' I suggest the released, currently 3.3.1 (the other option seems to be a nightly build, complicates comparison  between machines)
After download, unpack at some directory, by example prog/ffmpeg; then copy the dll's in prog/ffmpeg/bin to the directory with the pyglet ffmpeg player and test script; currently (pyglet repo)/examples/video_ffmpeg

Ubuntu:
Try in a terminal 'ffmpeg'; if it tells is not installed you can get it with
	sudo apt install ffmpeg
For ubuntu 17.04 I got version 3.2.4-1build2
(note: if a sample looks bad in the pyglet player, you could run 
	ffplay.exe <sample>
in a console to see if it should play well)


Other OS: please add the relevant info.

2. You need to have the samples, download the .zip with highest version available in
https://www.dropbox.com/sh/1hz8lwy5utmg4p7/AADVEUEfKqPqlbizVMSBP4nHa?dl=0

Unzip the samples, better if outside the pyglet repo clone.

3. Ensure your local pyglet copy is at branch ffmpeg
	cd repo_dir
	hg update ffmpeg
	
4. ensure the pyglet in repo_dir is seen by python

Preparation is complete.

Running the tests
-----------------

	cd repo_dir/examples/video_ffmpeg
	python3 run_test_suite.py <samples dir>
	
Each sample will be played and the media_player state along the play will be recorded.
The raw info collected would be in <samples_dir>\testun_00\dbg (or _01, _02 ... for subsequent runs)
This is the info a developer may ask when troubleshooting an issue, it also includes info about the OS, python version, pyglet version.

Additionally, a preliminary results analysis is writen to <samples_dir>/testrun_00/reports

For more detail and aptions look at the manual.

Windows note: In one machine has been observed that for each sample run it pop-ups an OS Message window with "C:\Windows\perf.dll not designed to run in Windows or it contains an error ..."; pressing the ok button will continue without noticeable problems. The same machine was running ok at some time; after a bunch of non-pyglet software updates this problem appeared. I will need some time to investigate this, but other than the anoying button click it seems to not cause problems.

Linux note: In one machine with Ubuntu 17.04 has been observed that for some testruns it pop-ups an OS Message window with "python3.5 crashed with SIGABRT in pa_mainloop_dispatch()", pressing the ok button testing continues at next sample.
Not always the same sample. Looks as a race condition, probably involving the code that sets a callback, because repeatdly playing a sample with media_player the console will eventually show a traceback with "Assertion 'c->callback' failed at pulsecore/socket-client.c:126, function do_call(). Aborting". The test_suite will retry to play crashed samples upto 5 times to get a clean debug reporting.
