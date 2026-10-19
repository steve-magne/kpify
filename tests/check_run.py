"""Check a kpify run's .kpify/ folder against a scenario's expected answers. Stdlib only.

    python3 tests/check_run.py <analysis-dir> <expected-dir> [--upto N]

--upto N checks stages 0..N only (default 5), for runs that stopped early.
Required headings (every `##` heading of each template) and KPI fields are read from skills/kpify/references/artifact-templates.md,
so the templates stay the single source of truth.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/explain-findings/scripts"))
from trace_numbers import close, prose_numbers  # noqa: E402  the skill's own check is the spec

TEMPLATES = ROOT / "skills/kpify/references/artifact-templates.md"
ARTIFACTS = ["01-analysis-brief.md", "02-data-profile.md", "03-kpi-catalog.md",
             "04-analysis.md", "05-visualization-review.md", "06-executive-summary.md"]


def stage(name):
    return int(name[:2]) - 1 if name[:2].isdigit() else 3  # kpi-results.json belongs to stage 3


def template_spec():
    parts = re.split(r"^## (0\d-[\w-]+\.md)$", TEMPLATES.read_text(), flags=re.M)
    sections = dict(zip(parts[1::2], parts[2::2]))
    headings = {name: re.findall(r"^(## [^<\n]+)$", body, re.M) for name, body in sections.items()}
    fields = [f for f in re.findall(r"^\| ([A-Z][\w ]*?) \|", sections["03-kpi-catalog.md"], re.M) if f != "Field"]
    return headings, fields


def check(analysis, expected, upto=5):
    """Return a list of (check name, passed, detail)."""
    analysis, expected = Path(analysis), Path(expected)
    headings, fields = template_spec()
    results = []
    texts = {}

    for name in ARTIFACTS:
        if stage(name) > upto:
            continue
        path = analysis / name
        if not path.exists():
            results.append((f"artifact {name}", False, "missing"))
            continue
        text = texts[name] = path.read_text()
        problems = []
        if not re.search(r"^Status: (complete|blocked)\b", text, re.M):
            problems.append("Status not complete/blocked")
        problems += [f"no '{h}'" for h in headings.get(name, []) if not re.search(rf"^{re.escape(h)}\b", text, re.M)]
        results.append((f"artifact {name}", not problems, "; ".join(problems)))

    if "03-kpi-catalog.md" in texts:
        blocks = re.split(r"^## KPI:", texts["03-kpi-catalog.md"], flags=re.M)[1:]
        missing = []
        for block in blocks:
            title = block.splitlines()[0].strip()
            empty = [f for f in fields if not re.search(rf"^\|\s*{f}\s*\|\s*[^|\s][^|]*\|", block, re.M)]
            if empty:
                missing.append(f"{title}: {', '.join(empty)}")
        results.append(("kpi catalog fields", bool(blocks) and not missing,
                        "no '## KPI:' blocks" if not blocks else "; ".join(missing)))

    if upto >= 3:
        results += check_values(analysis / "kpi-results.json", expected / "kpi-results.json")

    if upto >= 4:
        charts = [p.name for p in (analysis / "charts").glob("*") if not p.name.startswith(".")]
        review = texts.get("05-visualization-review.md", "")
        unreviewed = [c for c in charts if c not in review]
        results.append(("charts reviewed", bool(charts) and not unreviewed,
                        "no charts" if not charts else f"not in review: {unreviewed}"))

    for trap in json.loads((expected / "traps.json").read_text()):
        if max(stage(f) for f in trap["files"]) > upto:
            continue
        text = "\n".join(texts.get(f, "") for f in trap["files"])
        if "if" in trap and not re.search(trap["if"], text, re.I):
            results.append((f"trap {trap['id']}", True, "n/a"))
            continue
        misses = [p for p in trap.get("patterns", []) if not re.search(p, text, re.I)]
        if "forbid" in trap:  # lines matching "forbid" must also match "unless"
            misses += [line.strip() for line in text.splitlines()
                       if re.search(trap["forbid"], line, re.I) and not re.search(trap["unless"], line, re.I)]
        results.append((f"trap {trap['id']}", not misses, f"failed on: {misses}" if misses else ""))

    if upto >= 5 and "06-executive-summary.md" in texts:
        untraced = prose_numbers(texts, analysis / "kpi-results.json")
        results.append(("summary numbers traced", not untraced, f"not in results/profile/analysis: {untraced}"))
    return results


def check_values(actual_path, expected_path):
    if not actual_path.exists():
        return [("kpi-results.json", False, "missing")]
    try:
        rows = json.loads(actual_path.read_text())
    except json.JSONDecodeError as e:
        return [("kpi-results.json", False, f"invalid JSON: {e}")]
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        return [("kpi-results.json", False, "not a list of {id, period, value, …} rows")]
    results = []
    for exp in json.loads(expected_path.read_text()):
        candidates = [num(r.get("value")) for r in rows
                      if exp["period"] == "total" or period(r.get("period")) == exp["period"]]
        ok = any(v is not None and (close(v, x) or close(v / 100, x))  # accept percentages too
                 for v in candidates for x in exp["values"])
        if not ok and not exp.get("required", True):
            continue  # a KPI the prompt did not ask for: check it only when reported
        results.append((f"value {exp['id']} {exp['period']}", ok, "" if ok else f"expected one of {exp['values']}"))
    return results


def period(p):
    p = str(p or "")
    return p[:7] if re.match(r"\d{4}-\d{2}", p) else p


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis")
    ap.add_argument("expected")
    ap.add_argument("--upto", type=int, default=5)
    args = ap.parse_args()
    results = check(args.analysis, args.expected, args.upto)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
    failed = sum(not ok for _, ok, _ in results)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
