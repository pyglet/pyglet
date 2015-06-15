from future.utils import PY3

if PY3:
    from http.client import *
else:
    from httplib import *
    __future_module__ = True
