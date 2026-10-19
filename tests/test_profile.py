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

# Nested JSON: flattening, child tables, joins between differently named keys.
import json
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / "customers.json").write_text(json.dumps([{"id": f"c{i}", "plan": "pro"} for i in range(1, 5)]))
    orders = [{"id": f"o{i}", "customer": {"id": f"c{i % 4 + 1}"}, "tags": ["web", "promo"],
               "items": [{"sku": "A", "qty": 1}, {"sku": "B", "qty": 2}]} for i in range(1, 6)]
    orders.append({"id": "o9", "customer": {"id": "c99"}})  # orphan customer, no items
    (tmp / "orders.json").write_text(json.dumps({"data": orders}))
    out = subprocess.run([sys.executable, ROOT / "skills/profile-data/scripts/profile.py", tmp / "customers.json", tmp / "orders.json"],
                         capture_output=True, text=True, check=True).stdout
for expected in [
    "## orders.json.items",                                                  # list of objects → child table
    "- Rows: 10; columns: 3",                                                # 5 orders × 2 items, plus _parent_id
    "values: web, promo (5)",                                                 # list of scalars kept as one cell
    "| orders.json | customer.id | customers.json | id | 1 | 80.0% | N:1 |",  # nested key → differently named key
    "| orders.json.items | _parent_id | orders.json | id | 0 | 100.0% | N:1 |",
    't1 -- "customer.id → id (N:1)" --> t0',                                 # Mermaid edge
]:
    assert expected in out, f"missing: {expected}\n\n{out}"
print("ok json")

# API dumps: one page of a paginated response, and the same file name in two folders.
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    for month in ("2026-05", "2026-06"):
        (tmp / month).mkdir()
        (tmp / month / "orders.json").write_text(json.dumps(
            {"data": [{"id": f"{month}-{i}"} for i in range(3)], "meta": {"total": 7}, "links": {"next": "?page=2"}}))
    out = subprocess.run([sys.executable, ROOT / "skills/profile-data/scripts/profile.py", *sorted(tmp.glob("*/orders.json"))],
                         capture_output=True, text=True, check=True).stdout
for expected in [
    "## orders.json\n",
    "## 2026-06/orders.json",                                              # not overwritten
    "Possibly one page of a paginated API response: `next` = ?page=2; `total` = 7 but 3 rows",
]:
    assert expected in out, f"missing: {expected}\n\n{out}"
print("ok api")
