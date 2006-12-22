<?php 
$title = "About pyglet";
include("page_head.php");
?>

<p>Pyglet is a cross-platform multimedia library written in pure Python.
It uses built-in operating system facilities on Linux, Mac OS X
and Windows to provide windowing, drawing, event handling and so on.
Pyglet is the top layer in the following diagram:</p>

<table align="center" id="overview">
<tbody>
<TR class="pyglet">
    <TD title="Window opening and management including input devices"> Windows</TD>
    <TD title="Event management">Events</TD>
    <TD title="Image loading and saving (PNG, JPEG and others)">Images</TD>
    <TD title="Truetype text rendering with styles and layout">Text</TD>
    <TD title="High-level API for OpenGL graphics">2D &amp; 3D Graphics</TD>
    <TD title="GUI implemented over 2D and 3D graphics">GUI</TD>
</TR>
<tr><TD colspan="6" title="Python 2.4 or later">Python</TD></tr>
<tr><TD colspan="6" title="ctypes version 1.0 or later">ctypes</TD></tr>
<tr><TD colspan="2" title="Linux with OpenGL, gdk, freetype">Linux / X11</TD>
<TD colspan="2" title="Mac OS X 10.3 or later">Mac OS X</TD>
<TD colspan="2" title="Windows XP or later">Windows</TD></tr>
</tbody>
</table>

<p><strong>Pyglet is designed with the following goals:</strong></p>
<ol>
<li>Requirements for running are Python and ctypes.</li>
<li>No compilation.</li>
<li>Feature-full and easy to use API.</li>
<li>Fast enough for writing games.</li>
</ol>

<p><strong>The current status of pyglet is broadly:</strong></p>

<table id="status">
<tr><th>Component</th><th>Linux</th><th>Mac</th><th>Win</th><th>API</th></tr>
<tr><td>Windowing</td><td>Y*</td><td>Y</td><td>Y</td><td>alpha</td></tr>
<tr><td>Events</td><td colspan="3">Y</td><td>beta</td></tr>
<tr><td>Images</td><td>Y</td><td>Y</td><td>Y</td><td>alpha</td></tr>
<tr><td>Text</td><td>P</td><td>P</td><td>P</td><td>alpha</td></tr>
<tr><td>OpenGL</td><td>Y</td><td>Y</td><td>Y</td><td>solid</td></tr>
<tr><td>2D/3D API</td><td colspan="3">P</td><td>pre-alpha</td></tr>
<tr><td>GUI</td><td colspan="3">P</td><td>pre-alpha</td></tr>
<tr><td>Documentation</td><td colspan="3">N</td><td>-</td></tr>
</table>
<p>Notes:</p>
<ul>
<li>Y=Yes, N=No, P=Partial, "alpha" means it'll probably change, "beta"
means it probably won't change, "solid" means it's really not likely to
change at all. Probably.</li>
<li>A "Y" indicates that the implementation meets the current spec defined
in the requirements doc. We have some additional features we'd like to
implement (for example, changing screen modes, scroll event needs x,y of
mouse).</li>
<li>Linux windowing: older ATI drivers are buggy and work-arounds are not
yet written.</li>
</ul>

  </div>
  </body>
</html>
