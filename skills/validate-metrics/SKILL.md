---
name: validate-metrics
description: Use after KPIs are defined and before any chart or conclusion — or whenever data, a definition or a transformation changes. Computes every catalog KPI with reproducible code (analysis/kpis.py or .sql), reconciles it against the source (dedup counts, refunds, line totals, date bounds, denominators, partial periods), and writes analysis/04-analysis.md and analysis/kpi-results.json. A KPI that fails a check is reported UNVALIDATED, never silently.
allowed-tools: Bash(python3 *)
---

# validate-metrics — stage 3

Compute each KPI once, in code, and prove it against the source. Outputs: `analysis/kpis.py`
(or `analysis/kpis.sql`), `analysis/kpi-results.json` and `analysis/04-analysis.md`, following
`${CLAUDE_SKILL_DIR}/../kpify/references/artifact-templates.md`.

## Procedure

1. **Read the catalog and the profile** (`03-kpi-catalog.md`, `02-data-profile.md`). Each missing
   one → record `Assumed (no <file>): …` and the definition you used.
2. **Write the code.** One script computes every `defined` KPI exactly as its catalog entry says,
   per period and segment, and writes `kpi-results.json` itself. Use what the project has
   (Python stdlib `csv`/`sqlite3`, pandas, DuckDB); say which in `## Code` with the command to
   rerun. The code:
   - reads source files read-only and applies the profile's Transformations (dedup, refund
     split, exclusions) explicitly, each with a comment naming the profile issue number;
   - computes measures at their own grain (order totals from the order table, not summed over a
     join to order lines);
   - emits `BLOCKED` KPIs with `"value": null` and `"status": "blocked"`;
   - flags a partial period on its rows with `"note": "partial: n/N days"`.

   `kpi-results.json` is a flat list, one object per KPI × period × segment, nothing nested:

   ```json
   [
     {"id": "net_revenue", "period": "2026-05", "segment": "all", "value": 1234.5, "unit": "EUR", "status": "validated"},
     {"id": "conversion_rate", "period": "2026-05", "segment": "all", "value": null, "unit": "ratio", "status": "blocked"}
   ]
   ```
3. **Compute every derived number you will quote.** Per-day values, month-over-month deltas,
   shares, with/without an outlier, medians: if a later stage or the summary may cite it, the code
   produces it as a row in `kpi-results.json` (under a KPI id plus a suffix such as
   `net_revenue_per_day`) or in the Results table. No arithmetic by hand, in prose or in chat.
4. **Run the checks** below in the same script (assertions or a printed table) and copy each one
   into `## Validation checks` with expected value, actual value and pass/fail. Expected values
   come from the profile or an independent computation, not from the result being checked.
5. **Set statuses.** A KPI is `validated` only if every check touching it passed; otherwise
   `unvalidated`, with the failed check named in Limitations. Fix and rerun rather than
   relabel when the fix is clear.
6. **Write Findings** as two kinds of line: `Descriptive:` what the numbers show, with KPI ids
   and periods; `Diagnostic hypothesis:` a possible reason and the test that would confirm it.
   A difference between segments (promo vs not, new vs returning) is an association: write
   "associated with" or "correlation, not cause" on the same line.
7. **Revisit upstream if needed.** A check that reveals a wrong grain or definition reopens that
   stage (`## Revisions` there), then rerun this one.
8. **Set `Status: complete`** once the gate passes, then return to `kpify:kpify`.

## Checks

Run each that applies; add others the catalog's caveats call for.

| Check | What it compares |
|---|---|
| Row reconciliation | Raw rows − removed duplicates − excluded rows = rows used; removed count = profile count |
| Refund split | Gross − refunds = net, per period; refund rows counted separately from orders |
| Line totals | Sum of line amounts = order total, per order; mismatches counted (refund rows without lines are expected, not errors) |
| Grain | Order count from the order table = distinct order ids after the join |
| Date bounds | Min and max date used = profile date range; no row outside the window |
| Partial period | Coverage of each period; partial ones carry a `note` and are compared per day only |
| Denominators | Each ratio's denominator is non-zero and counts the population the catalog names (e.g. rows without a customer id excluded, count stated) |
| Independent recompute | One headline KPI recomputed by a second route (SQL vs Python, or summing another table) |

## Gate

- [ ] Headings exactly as in the template: `## Code`, `## Results`, `## Validation checks`,
      `## Findings`, `## Limitations`, `## Assumptions`, `## Revisions` (write "None." under an
      empty one).
- [ ] The code exists in `analysis/`, reruns with the command given, and writes
      `kpi-results.json` itself.
- [ ] Every catalog KPI has rows in `kpi-results.json`, under its catalog id; blocked ones with
      `null` values.
- [ ] Results table and `kpi-results.json` hold the same rows.
- [ ] Every number that later stages may quote is in `kpi-results.json` or `04-analysis.md`.
- [ ] Every applicable check ran, with expected, actual and pass/fail.
- [ ] Partial periods flagged in `kpi-results.json` (`note`) and in Limitations.
- [ ] Every Findings line is descriptive or a labeled hypothesis; no causal wording on a
      segment comparison.
- [ ] No source file modified.

## Red flags

| Thought | Reality |
|---|---|
| "The numbers look right" | Looking right is not a check. Reconcile against the source. |
| "I'll compute the per-day figure in the summary" | Derived numbers come from the code, or they cannot be traced. |
| "Join orders to lines to get revenue by product" | Sum line amounts for product revenue; never sum order totals over lines. |
| "One check failed but it's minor" | Then the KPI is `unvalidated`, and Limitations says why. |
| "June is lower than May" | June is partial. Compare per day, flag it. |
| "Promo orders are bigger, so the promo works" | An association. Selection can explain it; say so. |
| "I'll write the JSON by hand from the output" | The script writes it, so a rerun reproduces it. |
