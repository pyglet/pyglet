<?php 
$title = "Welcome to pyglet";
include("page_head.php");
?>

<p>Pyglet is a cross-platform multimedia library written in pure Python.
It uses built-in operating system facilities on Linux, Mac OS X
and Windows to provide windowing, drawing, event handling and so on.
Pyglet is the top layer in the following diagram:</p>

<table align="center" id="overview">
<tbody>
<TR class="pyglet">
    <TD title="Window opening and management"> Windows</TD>
    <TD title="Event management and handlers (incl. input devices)">Events</TD>
    <TD title="Image loading and saving (PNG, JPEG and others)">Images</TD>
    <TD title="Truetype text rendering with styles and layout">Text</TD>
    <TD title="2D and 3D high-performance graphics">OpenGL</TD>
    <TD title="3D geometric and file-based models">Models</TD>
</TR>
<tr><TD colspan="6" title="Python 2.4 or later">Python</TD></tr>
<tr><TD colspan="6" title="ctypes version 1.0 or later">ctypes</TD></tr>
<tr><TD colspan="2" title="Linux with OpenGL, gdk, freetype">Linux / X11</TD>
<TD colspan="2" title="Mac OS X 10.3 or later">Mac OS X</TD>
<TD colspan="2" title="Windows XP or later">Windows</TD></tr>
</tbody>
</table>


<?php include("news.php"); ?>
  </div>
  </body>
</html>
