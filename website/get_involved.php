<?php 
$title = "Get invoved in pyglet";
include("page_head.php");
?>

<p>Pyglet is still in very early development, but we are happy for people to pitch in. The most important help we can get at this time is for people to run the test suite on their system and let us know how it goes.</p>

<h2>Discuss</h2>
<p>Please sign up to the <a
href="http://groups.google.com/group/pyglet-users">mailing list</a> if
you're interested in pyglet, want to contribute or give us feedback.</p>

<h2>Try</h2>
<p>If you keen to try out pyglet then you may get the source from the <a
href="http://code.google.com/p/pyglet">subversion repository</a> at the
Google Code project site:</p>

<pre style="margin-left: 5em">svn checkout http://pyglet.googlecode.com/svn/trunk/ pyglet </pre>

<p>The most valuable thing that you can do when you've checked out the
source is run the test suite. You do this by being in the top level of the
checkout where the "LICENSE" file resides and typing:</p>

<pre style="margin-left: 5em">PYTHONPATH=. python tests/test.py</pre>

<p>The test runner will work through various aspects of pyglet including
windows, image loading and saving, text rendering, events, etc. Please sign
up to the mailing list above to give us feedback on your success running
the tests.</p>

</body>
</html>
