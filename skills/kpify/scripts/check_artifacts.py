"""Check the .kpify/ artifacts against artifact-templates.md and against each other. Stdlib only.

    python3 check_artifacts.py [DIR] [--stage N]       # DIR defaults to .kpify; N = 0..5
    python3 check_artifacts.py [DIR] --results-table   # print 04-analysis.md's Results table

Without --stage, checks every stage whose artifact exists. Per stage:
  all  Status line; every `##` heading of the template present and not empty ("None." counts)
  2    every KPI table field filled; KPI Status is `defined` or `BLOCKED: …`
  3    kpi-results.json is a flat list of {id, period, segment, value, unit, status} rows, status
       validated/unvalidated/blocked, value null exactly when blocked, one row per id × period × segment;
       every catalog id has rows, every row id is a catalog id (or id_suffix), blocked KPIs stay blocked;
       the Results table in 04-analysis.md is exactly the one --results-table prints
  4    every file in charts/ has a `## Chart: <file>` block, and every block's file exists
  5    every number in 06-executive-summary.md traces to a source (trace_numbers.py)
Prints failures only. Exit 0: all passed; 1: a check failed; 2: bad arguments.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "references/artifact-templates.md"
sys.path.insert(0, str(HERE.parent.parent / "explain-findings/scripts"))
from trace_numbers import prose_numbers  # noqa: E402

ARTIFACTS = ["01-analysis-brief.md", "02-data-profile.md", "03-kpi-catalog.md",
             "04-analysis.md", "05-visualization-review.md", "06-executive-summary.md"]
COMMON = ["## Assumptions", "## Revisions"]
KEYS = ["id", "period", "segment", "value", "unit", "status"]
STATUSES = {"validated", "unvalidated", "blocked"}
TABLE_HEAD = ["| KPI id | Period | Segment | Value | Unit | Status |", "|---|---|---|---|---|---|"]


def template_spec():
    """{artifact: required `##` headings}, KPI field names — both read from the templates."""
    parts = re.split(r"^## (0\d-[\w-]+\.md)$", TEMPLATES.read_text(), flags=re.M)
    sections = dict(zip(parts[1::2], parts[2::2]))
    headings = {name: re.findall(r"^(## [^<\n]+)$", body, re.M) + COMMON for name, body in sections.items()}
    fields = [f for f in re.findall(r"^\| ([A-Z][\w ]*?) \|", sections["03-kpi-catalog.md"], re.M) if f != "Field"]
    return headings, fields


def section(text, heading):
    """Body under a `##` heading up to the next one, or None when the heading is absent."""
    m = re.search(rf"^{re.escape(heading)}\b[^\n]*\n?(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m and m.group(1)


def catalog(text):
    """{kpi id: its block} from 03-kpi-catalog.md."""
    blocks = re.split(r"^## KPI:", text, flags=re.M)[1:]
    return {m.group(1): b for b in blocks if (m := re.match(r"\s*`?([\w.-]+)", b))}


def load_rows(path):
    """(rows, None) or (None, why not)."""
    if not path.exists():
        return None, "missing"
    try:
        rows = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        return None, "not a flat list of {id, period, segment, value, unit, status} rows"
    return rows, None


def results_table(rows):
    lines = list(TABLE_HEAD)
    for r in rows:
        status = str(r.get("status")) + (f" — {r['note']}" if r.get("note") else "")
        cells = [r.get("id"), r.get("period"), r.get("segment"), json.dumps(r.get("value")), r.get("unit"), status]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    return "\n".join(lines)


def check(analysis, stages=range(6), final=False):
    """Return a list of (check name, passed, detail). final=True also requires Status complete/blocked."""
    analysis = Path(analysis)
    headings, fields = template_spec()
    texts = {n: (analysis / n).read_text() for n in ARTIFACTS if (analysis / n).exists()}
    status = r"^Status: (complete|blocked)\b" if final else r"^Status: (draft|complete|blocked)\b"
    results = []

    for i in stages:
        name = ARTIFACTS[i]
        if name not in texts:
            results.append((f"artifact {name}", False, "missing"))
            continue
        problems = [] if re.search(status, texts[name], re.M) else \
            ["Status not complete/blocked" if final else "no 'Status: draft|complete|blocked' line"]
        for h in headings[name]:
            body = section(texts[name], h)
            if body is None:
                problems.append(f"no '{h}'")
            elif not body.strip():
                problems.append(f"'{h}' is empty (write \"None.\")")
        results.append((f"artifact {name}", not problems, "; ".join(problems)))

    kpis = catalog(texts.get("03-kpi-catalog.md", ""))
    if 2 in stages and "03-kpi-catalog.md" in texts:
        problems = []
        for kid, block in kpis.items():
            empty = [f for f in fields if not re.search(rf"^\|\s*{f}\s*\|\s*[^|\s][^|]*\|", block, re.M)]
            if empty:
                problems.append(f"{kid}: empty {', '.join(empty)}")
            elif not re.search(r"^\|\s*Status\s*\|\s*(defined\b|BLOCKED:)", block, re.M | re.I):
                problems.append(f"{kid}: Status must be 'defined' or 'BLOCKED: <reason>'")
        results.append(("kpi catalog fields", bool(kpis) and not problems,
                        "no '## KPI: <id> — <Name>' blocks" if not kpis else "; ".join(problems)))

    if 3 in stages:
        results += check_results(analysis, texts, kpis)

    if 4 in stages:
        charts = sorted(p.name for p in (analysis / "charts").glob("*") if p.is_file() and not p.name.startswith("."))
        blocks = [b.strip("` ") for b in re.findall(r"^## Chart:(.+)$", texts.get("05-visualization-review.md", ""), re.M)]
        problems = ([f"no '## Chart:' block for {c}" for c in charts if c not in blocks]
                    + [f"'## Chart: {b}' but no charts/{b}" for b in blocks if b not in charts])
        results.append(("charts reviewed", bool(charts) and not problems,
                        "no files in charts/" if not charts else "; ".join(problems)))

    if 5 in stages and "06-executive-summary.md" in texts:
        untraced = prose_numbers(texts, analysis / "kpi-results.json")
        results.append(("summary numbers traced", not untraced,
                        f"not in results/profile/analysis: {untraced} (run trace_numbers.py for the lines)"))
    return results


def check_results(analysis, texts, kpis):
    rows, error = load_rows(analysis / "kpi-results.json")
    if error:
        return [("kpi-results.json", False, error)]
    problems = []
    for i, r in enumerate(rows):
        where = f"row {i} ({r.get('id')} {r.get('period')} {r.get('segment')})"
        if missing := [k for k in KEYS if k not in r]:
            problems.append(f"{where}: no {', '.join(missing)}")
        value = r.get("value")
        if r.get("status") not in STATUSES:
            problems.append(f"{where}: status {r.get('status')!r} not one of {sorted(STATUSES)}")
        elif (r["status"] == "blocked") != (value is None):
            problems.append(f"{where}: value must be null exactly when status is blocked")
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            problems.append(f"{where}: value {value!r} is not a number")
    dups = [k for k, n in Counter((r.get("id"), r.get("period"), r.get("segment")) for r in rows).items() if n > 1]
    problems += [f"duplicate row {d}" for d in dups]
    # ponytail: first 10 problems only, so a broken file does not flood the agent's context.
    results = [("kpi-results.json rows", not problems, "; ".join(problems[:10]))]

    if kpis:
        ids = {r.get("id") for r in rows}
        blocked = {k for k, b in kpis.items() if re.search(r"^\|\s*Status\s*\|\s*BLOCKED", b, re.M | re.I)}
        problems = ([f"catalog id {k} has no row" for k in kpis if k not in ids]
                    + [f"row id {i} is not a catalog id or <id>_<suffix>" for i in sorted(ids, key=str)
                       if not any(i == k or str(i).startswith(k + "_") for k in kpis)]
                    + [f"{r['id']} is BLOCKED in the catalog but {r.get('status')} here" for r in rows
                       if r.get("id") in blocked and r.get("status") != "blocked"])
        results.append(("kpi ids match catalog", not problems, "; ".join(problems[:10])))

    if "04-analysis.md" in texts:
        body = section(texts["04-analysis.md"], "## Results") or ""
        actual = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
        expected = results_table(rows).splitlines()
        diff = [line for line in expected if line not in actual] + [line for line in actual if line not in expected]
        results.append(("results table = kpi-results.json", not diff,
                        f"{len(diff)} differing line(s), e.g. {diff[0]!r}; paste the output of --results-table" if diff else ""))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", nargs="?", default=".kpify", help="analysis folder (default: .kpify)")
    ap.add_argument("--stage", type=int, choices=range(6), help="check this stage only")
    ap.add_argument("--results-table", action="store_true", help="print the Results table from kpi-results.json")
    args = ap.parse_args()
    d = Path(args.dir)
    if not d.is_dir():
        ap.error(f"{d} is not a folder")

    if args.results_table:
        rows, error = load_rows(d / "kpi-results.json")
        if error:
            sys.exit(f"kpi-results.json: {error}")
        print(results_table(rows))
        return

    stages = [args.stage] if args.stage is not None else [i for i, n in enumerate(ARTIFACTS) if (d / n).exists()]
    results = check(d, stages)
    failed = [(name, detail) for name, ok, detail in results if not ok]
    for name, detail in failed:
        print(f"FAIL  {name}  — {detail}")
    print(f"{len(failed)} failure(s) in {len(results)} checks")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
