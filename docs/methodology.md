# kpify methodology

kpify's workflow is **adapted from [CRISP-DM](https://en.wikipedia.org/wiki/Cross-industry_standard_process_for_data_mining)**
(business understanding → data understanding → … → evaluation), trimmed to a BI question rather than a
modelling project and made explicit as files. It is inspired by CRISP-DM, not an implementation of it.
**kpify claims no compliance with CRISP-DM or any other standard.**

## Six stages

Each stage is one skill, writes one artifact to `analysis/` in the user's project, and has a gate:
a condition that must hold before the next stage may rely on it. Templates for every artifact live in
[`skills/kpify/references/artifact-templates.md`](../skills/kpify/references/artifact-templates.md).

| Stage | Skill | Artifact | Gate |
|---|---|---|---|
| 0 Frame | `frame-analysis` | `01-analysis-brief.md` | The decision, audience and questions are written down. At most 3 questions are asked, and only when the answer would change a KPI or a conclusion; otherwise the assumption is logged. |
| 1 Profile | `profile-data` | `02-data-profile.md` | No silent cleaning. Every transformation and every open data-quality issue is logged. |
| 2 Define | `define-kpis` | `03-kpi-catalog.md` | Each KPI has formula, numerator/denominator, unit, grain, window, baseline, source columns and caveats, or is marked `BLOCKED` (for instance, a missing denominator). |
| 3 Validate | `validate-metrics` | `04-analysis.md`, `kpi-results.json`, code | Each KPI has a reproducible calculation and named checks (totals reconciled, duplicates, denominators, date bounds); otherwise it is `UNVALIDATED`. |
| 4 Visualize | `choose-visuals` | `charts/`, `05-visualization-review.md` | Each chart names the question it answers and the KPI id it shows, and passes the review checklist. |
| 5 Explain | `explain-findings` | `06-executive-summary.md` | Each finding has observation, evidence, interpretation, confidence and next action. Every number in prose traces to `kpi-results.json` or a named check. No causal claim without a design that supports it; "no clear signal" is an allowed answer. |

The `kpify` entry skill reads `analysis/`, finds the current stage, announces it in one line and hands
off. Stages can also be run directly; a skipped upstream artifact is then recorded as an explicit
assumption.

## Iteration rule

The process is iterative, not a waterfall. When new evidence invalidates an earlier artifact (a grain
mismatch found during validation, a KPI that cannot answer the question), the earlier stage is reopened:
its status goes back to `draft` and a dated entry is appended to its `## Revisions` section saying
what changed, why, and which later artifacts are now stale. Earlier artifacts are never rewritten
silently.

## Principles

1. Business question before chart.
2. Definitions before calculations.
3. Profile before trusting.
4. Validate before visualizing.
5. Evidence before interpretation.
6. Reproducibility before polish.
7. Honest uncertainty over false precision.
8. Ask only when the answer materially affects the analysis.
9. Never silently invent definitions, targets, missing values, or causal explanations.
10. Every major output is inspectable and traceable to its source.

## Why files and gates

A baseline run of a plain agent on the acceptance scenario ([`tests/baseline.md`](../tests/baseline.md))
caught most data traps but failed on traceability: figures in prose that no validated calculation
produced, definitions that drifted between a table and a recommendation, an invented benchmark. Artifacts
make those failures visible, and the gates make them checkable by [`tests/check_run.py`](../tests/check_run.py).
