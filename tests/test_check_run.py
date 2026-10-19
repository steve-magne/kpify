"""Self-check for check_run.py: a synthetic perfect run passes, and each planted mistake fails.

    python3 tests/test_check_run.py
"""

import json
import tempfile
from pathlib import Path

from check_run import ARTIFACTS, check, template_spec
from check_artifacts import results_table

EXPECTED = Path(__file__).resolve().parent.parent / "examples/northwind-coffee/expected"

TRAP_TEXT = {
    "02-data-profile.md": "Data ends 2026-06-14, so June is a partial month.\n"
                          "24 exact duplicate rows found.\nOutlier: B2B bulk order O00526 for 1,920.00 EUR.\n",
    "03-kpi-catalog.md": "Net revenue = gross sales minus refunds.\n",
    "06-executive-summary.md": "June is incomplete (14 days). June net revenue: 6,377.10 EUR; 60% repeat rate.\n"
                               "Promo orders have higher AOV; this is a correlation, not a causal effect.\n"
                               "Conversion target: none supplied; 2% would be a hypothesis.\n",
}


def write_rows(root, rows):
    """Write kpi-results.json and its Results table in 04-analysis.md, as validate-metrics does."""
    (root / "kpi-results.json").write_text(json.dumps(rows))
    p = root / "04-analysis.md"
    text = p.read_text()
    start = text.index("## Results\n") + len("## Results\n")
    end = text.index("\n## ", start)
    p.write_text(text[:start] + results_table(rows) + "\n" + text[end:])


def perfect_run(root):
    headings, fields = template_spec()
    for name in ARTIFACTS:
        body = "\n\n".join(f"{h}\nx" for h in headings.get(name, []))
        (root / name).write_text(f"# {name}\n\nStatus: complete\n\n{body}\n\n{TRAP_TEXT.get(name, '')}")
    expected = json.loads((EXPECTED / "kpi-results.json").read_text())
    table = "| Field | Value |\n|---|---|\n" + "".join(f"| {f} | x |\n" for f in fields)
    table = table.replace("| Status | x |", "| Status | defined |")
    kpis = "".join(f"## KPI: {i} — {i}\n\n{table}\n" for i in dict.fromkeys(e["id"] for e in expected))
    kpis += "## KPI: conversion_rate — Conversion\n\n" + table.replace("| Status | defined |", "| Status | BLOCKED: no sessions |")
    p = root / "03-kpi-catalog.md"
    p.write_text(p.read_text().replace("Status: complete\n", "Status: complete\n\n" + kpis, 1))
    rows = [{"id": e["id"], "period": e["period"], "segment": "all", "value": e["values"][-1],
             "unit": e["unit"], "status": "validated"} for e in expected]
    rows.append({"id": "conversion_rate", "period": "total", "segment": "all", "value": None,
                 "unit": "ratio", "status": "blocked"})
    write_rows(root, rows)
    (root / "charts").mkdir()
    (root / "charts/net-revenue.png").write_bytes(b"")
    p = root / "05-visualization-review.md"
    p.write_text(p.read_text().replace("Status: complete\n", "Status: complete\n\n## Chart: net-revenue.png\n\nx\n", 1))
    return rows


def failures(root, upto=5):
    return [name for name, ok, _ in check(root, EXPECTED, upto) if not ok]


def skills_run_their_gate_check():
    skills = Path(__file__).resolve().parent.parent / "skills"
    for n, skill in enumerate(["frame-analysis", "profile-data", "define-kpis", "validate-metrics",
                               "choose-visuals", "explain-findings"]):
        text = (skills / skill / "SKILL.md").read_text()
        assert f"check_artifacts.py .kpify --stage {n}" in text, f"{skill}/SKILL.md gate does not run check_artifacts.py --stage {n}"
        assert "Bash(python3 *)" in text, f"{skill}/SKILL.md cannot run python3 without a prompt"


def main():
    skills_run_their_gate_check()
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        good_rows = perfect_run(root)
        assert failures(root) == [], failures(root)

        # Percentages are accepted as well as ratios.
        rows = json.loads(json.dumps(good_rows))
        rows[-2]["value"] *= 100
        write_rows(root, rows)
        assert failures(root) == [], failures(root)

        # Not deduplicating inflates revenue by ~2% -> value check fails.
        rows[0]["value"] *= 1.02
        write_rows(root, rows)
        assert failures(root) == ["value net_revenue 2026-01"], failures(root)

        # A Results table typed by hand drifts from kpi-results.json.
        (root / "kpi-results.json").write_text(json.dumps(good_rows))
        assert failures(root) == ["results table = kpi-results.json"], failures(root)
        write_rows(root, good_rows)

        # Broken rows: blocked with a value, a missing key, an id outside the catalog, a duplicate.
        bad = json.loads(json.dumps(good_rows))
        bad[-1]["value"] = 0.02
        del bad[0]["segment"]
        bad.append({**good_rows[1], "id": "sessions"})
        bad.append(dict(good_rows[2]))
        write_rows(root, bad)
        f = failures(root)
        assert {"kpi-results.json rows", "kpi ids match catalog"} <= set(f), f
        write_rows(root, good_rows)

        # An empty section, a KPI Status that is neither defined nor BLOCKED, a review block without its file.
        p = root / "02-data-profile.md"
        clean = p.read_text()
        p.write_text(clean.replace("## Lineage\nx", "## Lineage\n"))
        assert failures(root) == ["artifact 02-data-profile.md"], failures(root)
        p.write_text(clean)
        p = root / "03-kpi-catalog.md"
        clean = p.read_text()
        p.write_text(clean.replace("| Status | defined |", "| Status | maybe |", 1))
        assert failures(root) == ["kpi catalog fields"], failures(root)
        p.write_text(clean)
        p = root / "05-visualization-review.md"
        clean = p.read_text()
        p.write_text(clean + "\n## Chart: gone.png\n\nx\n")
        assert failures(root) == ["charts reviewed"], failures(root)
        p.write_text(clean)

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

        # A nested object instead of a list of rows fails cleanly.
        (root / "kpi-results.json").write_text(json.dumps({"months": {"2026-01": {"net_revenue": 1}}}))
        assert "kpi-results.json" in failures(root), failures(root)
        write_rows(root, good_rows)

        # --upto 1 only looks at stages 0-1.
        assert failures(root, upto=1) == ["artifact 01-analysis-brief.md"], failures(root, upto=1)
    print("ok")


if __name__ == "__main__":
    main()
