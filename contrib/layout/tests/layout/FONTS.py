#!/usr/bin/env python

'''Test font properties.

Text in each paragraph describes the intended result.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: INLINE_REPLACED.py 342 2006-12-29 16:38:23Z Alex.Holkner $'

import unittest
import base_layout

class FontsTest(base_layout.LayoutTestBase):
    xhtml = '''<?xml version="1.0"?>
    <html>
      <head>
        <style type="text/css">
          .b {font-weight: bold;}
          .i {font-style: italic;}
          .u {font-decoration: underline;}
          /*.sup {vertical-align: super;}
          .sub {vertical-align: sub;}*/
          .big {font-size: 36pt;}
          .small {font-size: 8pt;}
          .sans {font-family: Helvetica, Verdana, sans-serif}
          .serif {font-family: Georgia, 'Times New Roman', serif}
          .mono {font-family: 'Courier New', monospace}
        </style>
      </head>
      <body>
        <p>This is unstyled text.</p>
        <p class="b">This text is bold.</p>
        <p class="i">This text is italic.</p>
        <p class="u">This text is underlined.</p>
        <p>This text has a super<span class="sup">script</span> in it.</p>
        <p>This text has a sub<span class="sub">script</span> in it.</p>
        <p class="big">This text is 36pt.</p>
        <p class="small">This text is 8pt.</p>
        <p class="sans">This text is in Helvetica, Verdana or sans-serif</p>
        <p class="serif">This text is in Georgia, Times New Roman or serif</p>
        <p class="mono">This text is in Courier New or monospace</p>
      </body>
    </html>'''

if __name__ == '__main__':
    unittest.main()
