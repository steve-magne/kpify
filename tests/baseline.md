# Baseline — Northwind Coffee without kpify

Run: 2026-10-18, `tests/run_scenario.sh --baseline`, Claude Code headless (default model), 2 min 45 s.
Raw output kept in [`baseline-run/`](baseline-run/).
Environment: the maintainer's normal Claude Code setup (global CLAUDE.md, hooks and skills loaded,
reply language French). Not a clean-room run; rerun with the same setup when comparing.

Output: one chat answer and one script, `monthly_kpis.py` (stdlib, deduplicates, separates
refunds, normalises per day, has a `--check` self-test). No `.kpify/` artifacts, no chart.

## Traps

| Trap | Result | Evidence |
|---|---|---|
| Partial June | ✅ caught | Opens with it; per-day table; "June is a normal month" |
| Duplicate rows | ✅ caught | 30 found and removed |
| Refunds as negative rows | ✅ caught | Gross, refunds and net shown separately |
| Line grain | ✅ avoided | Revenue from `orders.csv`; matches the oracle |
| B2B outlier | ✅ caught | The 1,920 EUR order named as non-recurring |
| Conversion rate | ✅ blocked | "Not computable, sessions missing" |
| Promo correlation | ⚠️ partial | "Promotions don't drive anything" — a causal reading of a flat comparison |

## Numbers

The script's table matches `expected/kpi-results.json` exactly (net revenue, orders, gross AOV,
value-based refund rate). The **prose** around it does not:

| Claim in the answer | Actual | Error type |
|---|---|---|
| "June: 6,133 EUR" | 6,048.90 net after dedup (6,133.40 is the raw sum with duplicates) | Number from before cleaning |
| "22 of the 30 duplicates are in May" | 11 in May | Unverified claim |
| "Zero signups since February" | Last signup is 2026-01-01 | Unverified claim |
| Table headed "revenue/day" | Gross revenue/day, while the answer recommends *net* revenue/day | Definition drift |
| "Aim for 1.5–3% conversion in coffee e-commerce" | No source | Invented benchmark |
| "Acquisition is collapsing" | New-customer revenue does fall, but the cause is untested | Hypothesis stated as fact |

## What this means for kpify

A plain agent already catches the obvious data traps. Where it fails is **traceability**:
numbers in prose that no validated calculation produced, definitions that shift between table
and recommendation, benchmarks with no source, hypotheses presented as findings. So:

- `validate-metrics` and `explain-findings` must require every number in prose to come from
  `kpi-results.json` or a named check in `04-analysis.md`. Add a deterministic check for this
  to `check_run.py` (numbers in `06-executive-summary.md` must appear in the results).
- `define-kpis` must pin gross vs net (and other variants) once, and later stages must use the
  KPI id, not a loose label.
- The "no invented targets or benchmarks" rule needs a trap: add one to `traps.json`.
- The data-trap checks stay, but they are not where kpify adds most value.

## Fixture issue found

Every customer signed up on or before 2026-01-01, and the order pool is a fixed population, so
new-customer revenue falls by construction. The baseline's main "insight" (acquisition collapse)
is a generator artifact. Fix in `generate.py`: spread signups across the period and draw new
customers over time, then regenerate the expected answers.

**Fixed after this run** (same day): signups now spread over the period; data and expected
answers regenerated. The figures above refer to the first version of the fixture.
