#!/usr/bin/env python

'''Test inline replaced elements (specifically, images).  

Text before each image describes the intended result.  Use the mouse scroll
wheel to view the entire document.  
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import sys
import os
import base_layout

filename = os.path.join(os.path.split(__file__)[0], 'small_image.png')

class InlineReplacedTest(base_layout.LayoutTestBase):
    xhtml = '''<?xml version="1.0"?>
    <html>
      <head>
        <style type="text/css">
          p { margin: 0 }
        </style>
      </head>
      <body>
        <p>Margins around paragraphs have been removed for this test.</p>
        <p>This is the image without any styling: <img src="$IMGSRC" /></p>
        <p>With a 1px solid black border: <img src="$IMGSRC" 
            style="border: 1px solid;" /></p>
        <p>With a 10px solid black border: <img src="$IMGSRC" 
            style="border: 10px solid;" /></p>
        <p>With a 1px solid black border and 10px padding: <img src="$IMGSRC" 
            style="border: 1px solid; padding: 10px" /></p>
        <p>With a 1px solid black border and 10px margin: <img src="$IMGSRC" 
            style="border: 1px solid; margin: 10px" /></p>
        <p>With width=32px: <img src="$IMGSRC" 
            style="width:32px" /></p>
        <p>With height=32px: <img src="$IMGSRC" 
            style="height:32px" /></p>
        <p>With width=16px; height=32px: <img src="$IMGSRC" 
            style="width:16px; height:32px" /></p>
        <p>With width=20%: <img src="$IMGSRC" 
            style="width:20%" /></p>
        <p>With width=20%, min-width=50px, max-width=100px: <img src="$IMGSRC"
            style="width:20%; min-width:50px; max-width:100px" /></p>
        <p>With width=20%, min-height=50px, max-height=100px: 
            <img src="$IMGSRC" 
            style="width:20%; min-width:50px; max-width:100px" /></p>

      </body>
    </html>'''.replace('$IMGSRC', filename)

if __name__ == '__main__':
    unittest.main()
