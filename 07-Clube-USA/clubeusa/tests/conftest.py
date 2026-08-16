# tests/conftest.py
import sys, os
# tests/ agora vive dentro de clubeusa/, entao '..' e a raiz do projeto
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)                       # services, utils
sys.path.insert(0, os.path.join(ROOT, 'api'))  # deps, routers
