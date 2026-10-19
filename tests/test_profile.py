"""Known-answer check for skills/profile-data/scripts/profile.py on the Northwind Coffee fixture.

    python3 tests/test_profile.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "examples/northwind-coffee/data"

out = subprocess.run([sys.executable, ROOT / "skills/profile-data/scripts/profile.py", *sorted(DATA.glob("*.csv"))],
                     capture_output=True, text=True, check=True).stdout
for expected in [
    "Exact duplicate rows: 24 extra copies (1.8%)",     # orders.csv duplicates
    "| 2026-05 | 266 | 6 | 6 | 5 | 216 |",               # per-month breakdown: rows, dupes, refunds, blanks
    "last month 2026-06 covers 14/30 days",             # partial June
    "33 negative",                                      # refunds
    "max 1,920 (40×)",                                  # B2B outlier vs median order
    "| customer_id | text | 1.1% |",                    # guest checkouts
    "| order_items.csv | orders.csv | order_id | 0 | 33 | N:N |",  # line grain + refunds without lines
]:
    assert expected in out, f"missing: {expected}\n\n{out}"
print("ok")
