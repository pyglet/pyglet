<?php 
$title = "Get invoved in pyglet";
include("page_head.php");
?>

<p>Pyglet is still in very early development, but we are happy for people to pitch in. The most important help we can get at this time is for people to run the test suite on their system and let us know how it goes.</p>

<h2>Discuss</h2>
<p>Please sign up to the <a
href="http://groups.google.com/group/pyglet-users">mailing list</a> if
you're interested in pyglet, want to contribute or give us feedback.</p>

<h2>Prerequisites</h2>

<p>Python 2.4 with ctypes 1.0 <strong>or</strong> Python 2.5.</p>
<p>A video card capable of creating 24-bit or 32-bit OpenGL 1.1 contexts, or
better.</p>

<dl>
  <dt>Linux</dt>
  <dd>
    <ul>
      <li>Xlib <em>(what version?)</em></li>
      <li>GLX 1.3 or above (support for 1.2 is coming...)</li>
      <li>libgdk-x11-2.0</li>
      <li>libgdk_pixbuf-2.0</li>
    </ul>
  </dd>
  <dt>Mac OS X</dt>
  <dd>
    <ul>
      <li>10.3 or later.</li>
    </ul>
  </dd>
  <dt>Windows</dt>
  <dd>
    <ul>
      <li>XP or later (2000 and server editions are <em>not</em>
      supported).</li>
    </ul>
  </dd>
</dl>

<p>pyglet will use <a href="http://www.pythonware.com/products/pil/">PIL</a>
if it is installed, and is required only for saving images in formats other
than PNG and DDS.</p>

<p><a href="http://docutils.sourceforge.net/">docutils</a> is required to run the test suite.</p>

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
