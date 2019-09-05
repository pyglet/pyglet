pyglet website
==============

The pyglet website is a simple static site made with the *Lektor* CMS.
Lektor allows you to create static sites, but provides the ability to
edit them like a CMS. Lektor can be installed via pip::

    pip install lektor --user

To edit the site, first change to the "website" directory run::

    lektor server

Please see the documentation at https://getlektor.org for more information. 
Alternatively, if you do not wish to install or use Lektor, you can edit
the static **\*.lr** files directly.


After changing the website, it will be built and deployed automatically
when pushed to the repository.