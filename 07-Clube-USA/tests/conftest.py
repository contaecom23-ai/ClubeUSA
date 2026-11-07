# tests/conftest.py
import sys, os
_clubeusa = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'clubeusa'))
if _clubeusa not in sys.path:
    sys.path.insert(0, _clubeusa)
