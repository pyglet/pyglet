#!/usr/bin/env python

'''Test HTML formatting.

Text in each paragraph describes the intended result.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_layout

class HTMLTest(base_layout.LayoutTestBase):
    html = '''
    <html>
      <head>
        <style type="text/css">
          .BOLD {font-weight: bold}
          em {color: red}
        </style>
      </head>
      <body>
        <h1>HTML test</h1>
        <p>This is unstyled text.</p>
        <p>This words "<B>bold</B>" in this sentence have  
          <span class="BoLd">bold</span> weight (testing case
          insensitivity).</p>
        <p>This is <strong>strong</strong> and <em>emphasised</em> text.</p> 
        <p>This paragraph <b>has <i>mismatched</b> end</i> tags (any
          behaviour that doesn't crash is acceptable.</p>
        <HR>
        <p>There is an &lt;HR&gt; before this paragraph.</p>
        <p><font face="Courier New" size=7 color=blue>
          This has an HTML font tag, setting the face to courier, the size
          to 7 and the color to blue.</font></p>
        <p>This paragraph is not closed.
        <p>Neither is this one.
        <p><p>
        <p>There were several empty paragraphs before this one.
      </body>
    </html>'''

if __name__ == '__main__':
    unittest.main()
