"""
conftest.py
-----------
Root pytest configuration ensuring repo root is always in sys.path.
"""

import sys
import os

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
