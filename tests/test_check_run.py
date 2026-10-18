"""Self-check for check_run.py: a synthetic perfect run passes, and each planted mistake fails.

    python3 tests/test_check_run.py
"""

import json
import tempfile
from pathlib import Path

from check_run import ARTIFACTS, check, template_spec

EXPECTED = Path(__file__).resolve().parent.parent / "examples/northwind-coffee/expected"

TRAP_TEXT = {
    "02-data-profile.md": "Data ends 2026-06-14, so June is a partial month.\n"
                          "24 exact duplicate rows found.\nOutlier: B2B bulk order O00526 for 1,920.00 EUR.\n",
    "03-kpi-catalog.md": "Net revenue = gross sales minus refunds.\n",
    "06-executive-summary.md": "June is incomplete (14 days). June net revenue: 6,377.10 EUR; 60% repeat rate.\n"
                               "Promo orders have higher AOV; this is a correlation, not a causal effect.\n"
                               "Conversion target: none supplied; 2% would be a hypothesis.\n",
}


def perfect_run(root):
    headings, fields = template_spec()
    for name in ARTIFACTS:
        body = "\n\n".join(f"{h}\nx" for h in headings.get(name, []))
        (root / name).write_text(f"# {name}\n\nStatus: complete\n\n{body}\n\n{TRAP_TEXT.get(name, '')}")
    table = "| Field | Value |\n|---|---|\n" + "".join(f"| {f} | x |\n" for f in fields)
    with open(root / "03-kpi-catalog.md", "a") as f:
        f.write(f"\n## KPI: net_revenue — Net revenue\n\n{table}\n"
                f"## KPI: conversion_rate — Conversion\n\n{table.replace('| Status | x |', '| Status | BLOCKED: no sessions |')}")
    rows = [{"id": e["id"], "period": e["period"], "value": e["values"][-1], "status": "validated"}
            for e in json.loads((EXPECTED / "kpi-results.json").read_text())]
    (root / "kpi-results.json").write_text(json.dumps(rows))
    (root / "charts").mkdir()
    (root / "charts/net-revenue.png").write_bytes(b"")
    with open(root / "05-visualization-review.md", "a") as f:
        f.write("## Chart: net-revenue.png\n")


def failures(root, upto=5):
    return [name for name, ok, _ in check(root, EXPECTED, upto) if not ok]


def main():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        perfect_run(root)
        assert failures(root) == [], failures(root)

        # Percentages are accepted as well as ratios.
        rows = json.loads((root / "kpi-results.json").read_text())
        rows[-1]["value"] *= 100
        (root / "kpi-results.json").write_text(json.dumps(rows))
        assert failures(root) == [], failures(root)

        # Not deduplicating inflates revenue by ~2% -> value check fails.
        rows[0]["value"] *= 1.02
        (root / "kpi-results.json").write_text(json.dumps(rows))
        assert failures(root) == ["value net_revenue 2026-01"], failures(root)

        # A draft artifact, a missing KPI field and an unreviewed chart all fail.
        p = root / "01-analysis-brief.md"
        p.write_text(p.read_text().replace("Status: complete", "Status: draft"))
        p = root / "03-kpi-catalog.md"
        p.write_text(p.read_text().replace("| Denominator | x |", "| Denominator |  |", 1))
        (root / "charts/extra.png").write_bytes(b"")
        f = failures(root)
        assert {"artifact 01-analysis-brief.md", "kpi catalog fields", "charts reviewed"} <= set(f), f

        # A summary number no calculation produced, and an unsourced benchmark, both fail.
        p = root / "06-executive-summary.md"
        clean = p.read_text()
        p.write_text(clean + "June revenue was 6,133.40 EUR.\nAim for 1.5-3% conversion, the industry norm.\n")
        f = failures(root)
        assert {"summary numbers traced", "trap no_invented_benchmark"} <= set(f), f
        p.write_text(clean)

        # --upto 1 only looks at stages 0-1.
        assert failures(root, upto=1) == ["artifact 01-analysis-brief.md"], failures(root, upto=1)
    print("ok")


if __name__ == "__main__":
    main()
