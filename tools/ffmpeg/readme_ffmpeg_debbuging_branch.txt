This changeset starts from dangillet/pyglet, branch ffmpeg
	changeset:   3621:42a8441d7950
	branch:      ffmpeg
	tag:         tip
	user:        Daniel Gillet <dan.gillet737@gmail.com>
	date:        Tue Apr 11 10:39:59 2017 +0200
	files:       pyglet/media/drivers/openal/adaptation.py
	description:
	Fix bug in OpenAL
	
( https://bitbucket.org/dangillet/pyglet )


Goals

 - better capture of debbuging info
	More player state captured, less perturbation in timings by capturing raw info and save after play

- support postprocessing of debuggging info into different views / reports
    Player state captured can be postprocessed in a varity of reports; easy to define new reports.
	Reports can be rendered for raw data captured in another machine.

- have some quality measure to programatically compare two test runs and tell which is better
    Rought sketch ATM, qtty of anomalies over all samples in the debbuging session.
	Useful to tell if a change in code or library gives better or worse results.

- enforce an ordered schema to store test results
	Avoids mixing results obtained under different settings.
	Consistent access to debug data captured by different persons or under different conditions.

See readme_run_test.txt for the instructions a tester or user will need to follow to send debug info.

See the manual.txt initial sections for dev workflows and basic descriptions.
