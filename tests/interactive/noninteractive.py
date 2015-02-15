"""
Start the interactive tests in non interactive mode. Runs unittest.main after setting a flag to
switch to noninteractive mode.

There are two goals for noninteractive mode:
    - Simply verify there are no exceptions/crashes during the test cases
    - Take screenshots of the verification moments and if possible compare them to regression
      images
"""
import unittest

_run_interactive = True

def run_interactive():
    return _run_interactive

if __name__ == '__main__':
    _run_interactive = False
    unittest.main()


