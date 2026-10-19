---
name: define-kpis
description: Use after the data is profiled and before computing any KPI — or whenever a metric's meaning, a target or the question changes. Turns the brief's questions into a catalog of KPIs, each with formula, numerator and denominator, unit, grain, time window, baseline, filters, target, owner and caveats, pins variants such as gross vs net under one id, and marks anything the data cannot support BLOCKED. Writes .kpify/03-kpi-catalog.md.
allowed-tools: Bash(python3 *)
---

# define-kpis — stage 2

Decide exactly what each number means before calculating it. Output: `.kpify/03-kpi-catalog.md`,
following `${CLAUDE_SKILL_DIR}/../kpify/references/artifact-templates.md`. Vocabulary and field
rules: `${CLAUDE_SKILL_DIR}/../kpify/references/kpi-definition.md`.

## Procedure

1. **Read the brief and the profile** (`01-analysis-brief.md`, `02-data-profile.md`). Each missing
   one → record `Assumed (no <file>): …` under Assumptions.
2. **List candidate metrics per question.** For each question in the brief: which metric answers
   it, and which ones the user asked to track. Keep a KPI only if it supports the brief's
   decision; everything else is a metric (`Type | metric`) or left out.
3. **Give each KPI a stable id** in `snake_case` (`net_revenue`, `refund_rate`). The id is the
   contract: `kpi-results.json`, charts and the summary use it, never a loose label.
4. **Pin variants.** When a metric has defensible variants (gross vs net, by count vs by value,
   mean vs median, with vs without an outlier), choose one per id and say which in Formula.
   Need two? Two ids. A variant that changes the answer to a question is an open point: record
   it as an assumption with its impact.
5. **Fill every field** of the template for every KPI, in its two-column table, one row per
   field, field names verbatim (the checker reads them):

   ```markdown
   ## KPI: net_revenue — Net revenue

   | Field | Value |
   |---|---|
   | Type | KPI |
   | Meaning | … |
   …one row for each template field, through Status…
   ```

   A field that does not apply gets a reason (`n/a — not a ratio`), never a blank. In particular:
   - **Filters and Transformations** name the profile's issues by number: duplicates removed,
     refunds in or out, rows without a key excluded, outliers kept or not.
   - **Time window** says calendar month, rolling or to-date, and how a partial period is
     treated (flagged, compared per day, or excluded). Never compared raw to full periods.
   - **Baseline** names the comparison (prior full month, same days of the prior month…).
   - **Target**: the user's value quoted with its source, else `none supplied`, else
     `hypothesis: <value> — <reasoning>`. Same rule for any benchmark mentioned anywhere.
   - **Owner**: the person the user named, else `unassigned — not supplied`. Never invent one.
6. **Mark what the data cannot support** `BLOCKED: <missing input> — <data that would unblock
   it>`. A requested ratio with no denominator (conversion rate without sessions) stays in the
   catalog, blocked; it is not estimated or replaced by a proxy.
7. **Compute nothing.** Values belong to stage 3. If defining a KPI shows the brief or profile is
   wrong, add a `## Revisions` entry there.
8. **Set `Status: complete`** once the gate passes, then return to `kpify:kpify`.

## Gate

- [ ] `python3 ${CLAUDE_SKILL_DIR}/../kpify/scripts/check_artifacts.py .kpify --stage 2` prints 0 failures
      (one `## KPI: <id> — <Name>` block per KPI, every field filled, Status `defined` or
      `BLOCKED: …`, `## Assumptions` and `## Revisions` not empty). Fix every FAIL line and rerun.
- [ ] Every KPI traces to a question or a tracking request in the brief.
- [ ] Each variant (gross/net, count/value, mean/median) is pinned under one id, named in Formula.
- [ ] Ratios state numerator and denominator; a missing input makes the KPI `BLOCKED` with the
      missing data named.
- [ ] Every Target is quoted from the user, `none supplied`, or `hypothesis: … — reasoning`.
      No unsourced benchmark or percentage next to "target", "typical" or "industry".
- [ ] Every Owner is a person the user named, or `unassigned — not supplied`.
- [ ] Each profile issue that affects a KPI is handled in its Filters or Transformations.
- [ ] No values computed yet.

## Red flags

| Thought | Reality |
|---|---|
| "Revenue is revenue" | Gross or net, order or line grain, with or without refunds. Pin it under an id. |
| "Nobody owns it, I'll leave Owner blank" | Write `unassigned — not supplied`. A blank field fails the gate. |
| "The CEO probably owns revenue" | Never infer an owner. Only the user names one. |
| "2–3% is a normal conversion rate" | An unsourced benchmark. `none supplied`, or a labeled hypothesis. |
| "No sessions, so I'll use orders per customer instead" | A proxy hides the gap. `BLOCKED`, name the missing data. |
| "I'll decide gross vs net when I see the numbers" | Choosing after seeing results is picking the answer. Decide now. |
