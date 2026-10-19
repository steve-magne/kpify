---
name: kpify
description: Use before any data analysis, KPI, metric, dashboard, BI report or chart work — exploring CSV/Excel/Parquet/JSON files or a SQL database, deciding what to measure, explaining why a metric changed, or auditing existing metrics and charts. Finds where the analysis stands in .kpify/ and routes to the right kpify stage skill so nothing is calculated or charted before the question, data and definitions are clear.
---

# kpify — analysis router

kpify turns raw data into validated KPIs and decision-ready findings through six stages.
Each stage has its own skill and writes one artifact to `.kpify/` in the user's project.
Your job here: find the current stage, tell the user in one line, and hand off.

## The rule

**No number or chart reaches the user before its stage gates have passed.**
A quick chart from unframed, unprofiled data is the failure kpify exists to prevent.
If the user insists on skipping ahead, do it, but label the output `UNVALIDATED` and say
which stages were skipped.

## Stages

| # | Skill | Artifact | Gate to leave the stage |
|---|---|---|---|
| 0 | `kpify:frame-analysis` | `01-analysis-brief.md` | Decision, audience, questions, scope written; open questions answered or logged as assumptions |
| 1 | `kpify:profile-data` | `02-data-profile.md` | Every source inventoried and traced to its origin; grain, keys, joins diagram, quality issues recorded; no silent cleaning |
| 2 | `kpify:define-kpis` | `03-kpi-catalog.md` | Every KPI fully defined (see `${CLAUDE_SKILL_DIR}/references/kpi-definition.md`) or marked `BLOCKED` |
| 3 | `kpify:validate-metrics` | `04-analysis.md`, `kpi-results.json`, code | Every reported KPI has reproducible code and passed checks, or is marked `UNVALIDATED` |
| 4 | `kpify:choose-visuals` | `charts/`, `05-visualization-review.md` | Every chart names its question and KPI id and passes `${CLAUDE_SKILL_DIR}/references/chart-review-checklist.md` |
| 5 | `kpify:explain-findings` | `06-executive-summary.md` | Every finding has observation, evidence, interpretation, confidence, next action |

Artifact formats: `${CLAUDE_SKILL_DIR}/references/artifact-templates.md`. Shared vocabulary (metric, KPI, target,
dimension, grain): `${CLAUDE_SKILL_DIR}/references/kpi-definition.md`.

## Procedure

1. **Locate state.** List `.kpify/` in the project root. For each artifact present, read its
   `Status:` line (`draft`, `complete`, `blocked`). No `.kpify/` folder → stage 0.
2. **Pick the stage.** The first stage whose artifact is missing or not `complete` — unless the
   request targets a specific stage (see Direct entry).
3. **Check for staleness.** If the user's request changes the question, the data, or a KPI
   definition, the earliest affected stage is the current stage. Say so.
4. **Announce** in one line: `kpify: stage N (<skill>) — <why>`.
5. **Invoke** that stage skill and follow it. When it completes, return here and repeat.

Stop after stage 5, or earlier when the user only asked for an earlier stage's output
(e.g. "what should we measure?" ends after stage 2).

## Direct entry

Users may call one stage directly, e.g. to define KPIs for data they already understand or to
review an existing chart. Allow it. The stage skill must then record each missing upstream
artifact as an explicit assumption in its own artifact (`Assumed (no 01-analysis-brief.md): …`).

## Iteration

Going back is normal. When new evidence invalidates an earlier artifact (a grain mismatch found
during validation, a KPI that cannot answer the question), reopen that stage, set its
`Status: draft`, and append to its `## Revisions` section: date, what changed, why, which later
artifacts are now stale. Never rewrite an earlier artifact silently.

## Red flags — stop and route back

| Thought | Reality |
|---|---|
| "The user just wants a quick chart" | A chart is a claim. Route through framing, or label it `UNVALIDATED`. |
| "The KPI is obvious, no need to define it" | Revenue: gross or net? Per order or per line? Define it. |
| "I'll clean the data as I go" | Unlogged cleaning is unreproducible. Record it in the profile. |
| "This explains the drop" | Is the period complete? Is it causal? Evidence first. |
| "I'll pick a reasonable target" | Targets come from the user or are labeled as hypotheses. |
| "The numbers look right" | Looking right is not a check. Reconcile against the source. |
