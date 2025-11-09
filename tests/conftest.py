import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
src = os.path.join(ROOT, 'src')
if src not in sys.path:
    sys.path.insert(0, src)
