---
name: explain-findings
description: Use after metrics are validated and charted, before telling anyone what the data shows — or whenever asked to explain a change, summarize results or recommend next steps. Writes .kpify/06-executive-summary.md with a short answer, then each finding as observation, evidence, interpretation, confidence and next action, quoting only numbers already in kpi-results.json, 02-data-profile.md or 04-analysis.md, wording correlations as associations, and stating what the data cannot tell us.
allowed-tools: Bash(python3 *)
---

# explain-findings — stage 5

Say what the evidence supports, and no more. Output: `.kpify/06-executive-summary.md`,
following `${CLAUDE_SKILL_DIR}/../kpify/references/artifact-templates.md`. Your chat answer is a
short version of this file, never a different story.

## Procedure

1. **Read everything upstream**: `01-analysis-brief.md` (the questions and the decision),
   `02-data-profile.md`, `03-kpi-catalog.md`, `04-analysis.md`, `kpi-results.json`,
   `05-visualization-review.md`. Each missing one → record `Assumed (no <file>): …`.
2. **Answer each question in the brief**, in order. One finding per answer; add a finding only
   for something the decision needs. "No clear signal" is a finding: say what was compared and
   that the difference is within noise or too small to act on.
3. **Quote, never compute.** Every number in the summary is copied from `kpi-results.json`,
   `02-data-profile.md` or `04-analysis.md`, as written there or rounded from it; a ratio may be
   shown as a percentage. A difference, share, per-day value, count or "x times" you want and
   cannot find there is not written: go back to `kpify:validate-metrics`, add it to the code,
   rerun, then quote it. No arithmetic in your head, in the summary or in chat.
4. **Write each finding** with all five fields:

   ```markdown
   ### June revenue did not collapse; the month is partial

   - Observation: June net revenue per day is in line with May; the June total covers 14 of 30 days.
   - Evidence: net_revenue_per_day 2026-05 = <value> EUR, 2026-06 = <value> EUR (04-analysis.md
     Results; charts/net-revenue-per-day.png). Data ends 2026-06-14 (02-data-profile.md).
   - Interpretation: the "drop" is mostly the shorter period, not lower daily sales.
   - Confidence and caveats: high on the per-day comparison; two weeks is a short window.
   - Next action: compare full June when the data is complete; report partial months per day.
   ```

   - **Evidence** names the KPI id, period, segment and value, and the source file or chart.
   - **Interpretation** of a segment difference (promo vs not, new vs returning) is an
     association: write "associated with" or "correlation, not cause" on the same line, and
     give the test that would establish cause (an A/B test, a holdout, a before/after with a
     control) as the next action.
   - **Confidence**: high / medium / low, and why (validated or not, sample size, partial
     period, outliers).
   - **Next action** is a decision or a check someone can do, with its owner only if the user
     named one.
5. **Write `## Summary`** last: three sentences or fewer that answer the brief's questions with
   the findings' own wording and numbers. A partial period is called partial right there.
6. **Write `## What the data cannot tell us`**: every `BLOCKED` KPI with the data that would
   unblock it, every causal question left open, every assumption that would change a finding.
   No target or benchmark appears anywhere unless the user supplied it or it is labeled a
   hypothesis.
7. **Trace the numbers** and fix every line it reports, then rerun until it prints 0:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/trace_numbers.py .kpify
   ```

   Fix by quoting the source value, by adding the number to the stage 3 code, or by deleting it.
   Never by adding it to `04-analysis.md` by hand.
8. **Set `Status: complete`** once the gate passes, then **answer in chat** from the summary:
   the same findings, the same numbers, the same caveats, and the path to the file.

## Gate

- [ ] Headings exactly as in the template: `## Summary`, `## Findings` (one `###` per finding),
      `## What the data cannot tell us`, `## Assumptions`, `## Revisions` (write "None." under
      an empty one).
- [ ] Every question in the brief is answered by a finding or listed under what the data cannot
      tell us.
- [ ] Every finding has Observation, Evidence, Interpretation, Confidence and caveats, Next action.
- [ ] `trace_numbers.py` reports 0 untraced numbers.
- [ ] Partial periods are called partial wherever they are compared.
- [ ] No causal wording on a correlation; each causal hypothesis comes with its test.
- [ ] Every `BLOCKED` KPI appears under what the data cannot tell us, with the missing data.
- [ ] The chat answer says what the summary says.

## Red flags

| Thought | Reality |
|---|---|
| "May minus June is easy, I'll just write it" | A hand-computed number cannot be traced. Add it to the code, or leave it out. |
| "Roughly 47 orders, close enough" | If it is not in the results, profile or analysis, it does not go in the summary. |
| "Revenue dropped in June" | June is partial. Say per day, and say partial. |
| "Promo customers spend more, so the promo works" | Associated with. Selection can explain it; the test is an A/B or holdout. |
| "I found nothing, I need something to say" | "No clear signal" is a valid, useful finding. |
| "Conversion is probably around 2%" | Conversion is `BLOCKED`. Say which data would unblock it. |
| "The chat answer can be punchier than the file" | Same findings, same numbers. The file is the source. |
