"""Check a kpify run's .kpify/ folder against a scenario's expected answers. Stdlib only.

    python3 tests/check_run.py <analysis-dir> <expected-dir> [--upto N]

--upto N checks stages 0..N only (default 5), for runs that stopped early.
Structure (headings, KPI fields, kpi-results.json rows, Results table, charts, traced numbers) is checked by
skills/kpify/scripts/check_artifacts.py, the same script the skills' gates run, so the skills' checks are the
spec for this harness. On top of it: Status complete, values against the oracle, and the scenario's traps.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/kpify/scripts"))
from check_artifacts import ARTIFACTS, check as check_artifacts, load_rows, template_spec  # noqa: E402,F401
from trace_numbers import close  # noqa: E402  put on sys.path by check_artifacts


def stage(name):
    return int(name[:2]) - 1 if name[:2].isdigit() else 3  # kpi-results.json belongs to stage 3


def check(analysis, expected, upto=5):
    """Return a list of (check name, passed, detail)."""
    analysis, expected = Path(analysis), Path(expected)
    results = check_artifacts(analysis, range(upto + 1), final=True)
    texts = {n: (analysis / n).read_text() for n in ARTIFACTS if stage(n) <= upto and (analysis / n).exists()}

    if upto >= 3:
        results += check_values(analysis / "kpi-results.json", expected / "kpi-results.json")

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
    return results


def check_values(actual_path, expected_path):
    rows, error = load_rows(actual_path)
    if error:
        return []  # check_artifacts already reports it
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
