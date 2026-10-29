"""
Dismiss SmartCenter type-r (report ready) notifications.

Run from repo root:
  python scripts/revnext/dismiss_report_notifications.py --dry-run
  python scripts/revnext/dismiss_report_notifications.py --limit 100
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "revnext"))

from revnext.notifications import _cli

if __name__ == "__main__":
    raise SystemExit(_cli())
