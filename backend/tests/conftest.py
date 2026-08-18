"""Test bootstrap.

Adds the backend root to ``sys.path`` so tests run with a bare ``pytest`` from anywhere,
with no install step and no environment variables.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
