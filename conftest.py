"""Pytest bootstrap for the monorepo.

Adding the backend package to ``sys.path`` keeps the tests readable while the
repository stays lightweight and framework-agnostic.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent
BACKEND_PATH = ROOT / "backend"
LOCAL_TMP = ROOT / ".tmp" / "pytest-temp"
LOCAL_TMP.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("TEMP", str(LOCAL_TMP))
os.environ.setdefault("TMP", str(LOCAL_TMP))
os.environ.setdefault("TMPDIR", str(LOCAL_TMP))
tempfile.tempdir = str(LOCAL_TMP)

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))
