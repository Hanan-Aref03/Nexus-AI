"""Pytest bootstrap for the repository's canonical test tree.

Keeping the test wiring under ``tests/`` makes the repo structure easier to
scan: production code lives under ``backend/`` and every automated check lives
under one test root.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))
