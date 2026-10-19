# Artifact templates

Every artifact lives in `.kpify/` and starts with the same header. Keep every `##` heading
below with its exact text, in English, even when the content is in another language:
`scripts/check_artifacts.py` looks for them, and every
stage's gate runs it.

```markdown
# <Title>

Status: draft | complete | blocked
Updated: YYYY-MM-DD
Inputs: <upstream artifacts and data files this depends on>
```

Every artifact ends with:

```markdown
## Assumptions
- <assumption> — <why it is reasonable> — <what would change if wrong>

## Revisions
- YYYY-MM-DD — <what changed> — <why> — <stale downstream artifacts>
```

Write "None." under an empty section rather than deleting it.

---

## 01-analysis-brief.md

```markdown
## Decision
<The decision or action this analysis informs. One or two sentences.>

## Audience
<Who reads the result and what they can act on.>

## Questions
1. <Specific question the data must answer>

## Scope
- Period: <start – end, timezone if relevant>
- Granularity: <day / week / month; entity>
- In / out of scope: <segments, products, regions>

## Known definitions
<Definitions the user supplied. Quote them; do not paraphrase.>

## Data available
<Sources and access limits.>

## Open questions
- <question> — asked | assumed: <assumption>
```

## 02-data-profile.md

````markdown
## Sources
| Source | Rows | Columns | Grain (one row = …) | Date range | Key |
|---|---|---|---|---|---|

## Columns
| Source.column | Type | Role (id / dimension / measure / date) | Nulls % | Distinct | Notes |
|---|---|---|---|---|---|

## Relationships
<Join keys, cardinality (1:1, 1:N), orphans found.>

```mermaid
flowchart LR
  api0["GET /v1/orders"] --> t0["orders.json"]
  t0 -- "customer.id → id (N:1)" --> t1["customers.json"]
```

## Lineage
| Source | Produced by (path:line) | Endpoint / query | Fields dropped | Fixed parameters |
|---|---|---|---|---|

Data worth fetching:
| Data | Endpoint / field | Question it serves | Status (confirmed: code / docs, or hypothesis) |
|---|---|---|---|

## Quality issues
| # | Issue | Evidence (count, example) | Impact | Handling |
|---|---|---|---|---|

Handling is one of: `open`, `transformed (see below)`, `accepted (reason)`.

## Transformations
| # | Transformation | Rows affected | Reason | Reversible? |
|---|---|---|---|---|

## Observations vs hypotheses
- Observed: <fact with count>
- Hypothesis: <possible explanation, not yet tested>
````

## 03-kpi-catalog.md

One block per KPI. Field list and vocabulary: `kpi-definition.md`.

```markdown
## KPI: <id> — <Name>

| Field | Value |
|---|---|
| Type | KPI / metric |
| Meaning | |
| Decision supported | |
| Formula | |
| Numerator | |
| Denominator | |
| Unit | |
| Aggregation | |
| Grain | |
| Dimensions | |
| Filters | |
| Time window | |
| Baseline | |
| Target | <user-supplied value, or "none supplied", or "hypothesis: …"> |
| Source columns | |
| Transformations | <refs to profile transformations> |
| Caveats | |
| Owner | <person named by the user, or "unassigned — not supplied"> |
| Confidence | high / medium / low — <why> |
| Status | defined / BLOCKED: <reason> |
```

## 04-analysis.md

```markdown
## Code
<Path(s) to the SQL / Python that computes every KPI, and the command to rerun it.>

## Results
<Output of `check_artifacts.py .kpify --results-table`, pasted as is: one row per kpi-results.json row.>
| KPI id | Period | Segment | Value | Unit | Status |
|---|---|---|---|---|---|

## Validation checks
| # | KPI id | Check | Expected | Actual | Pass? |
|---|---|---|---|---|---|

## Findings
- Descriptive: <what the numbers show>
- Diagnostic hypothesis: <possible reason, and the test that would confirm it>

## Limitations
<Sample size, incomplete periods, unvalidated results.>
```

### kpi-results.json

Same rows as the Results table, machine-readable:

```json
[
  {"id": "net_revenue", "period": "2026-01", "segment": "all",
   "value": 12345.67, "unit": "EUR", "status": "validated"},
  {"id": "net_revenue_per_day", "period": "2026-06", "segment": "all",
   "value": 412.30, "unit": "EUR/day", "status": "validated", "note": "partial: 14/30 days"}
]
```

`status` is one of `validated`, `unvalidated`, `blocked` (`value` is `null` when blocked).
`id` is a KPI id from `03-kpi-catalog.md`. `note` is optional; use it to flag a partial period
or another caveat on that row.

## 05-visualization-review.md

```markdown
## Chart: <file in charts/>

- Question: <the question it answers>
- KPI ids: <ids from 03-kpi-catalog.md>
- Chart type and why: <see chart-selection.md>
- Checklist: <pass, or the items that failed and the fix>
```

## 06-executive-summary.md

```markdown
## Summary
<Three sentences or fewer: the answer to the brief's questions.>

## Findings

### <Finding title>
- Observation:
- Evidence: <value, comparison, period, segment; link to 04-analysis.md row or chart>
- Interpretation:
- Confidence and caveats:
- Next action:

## What the data cannot tell us
<Questions left open, blocked KPIs, causal claims not supported.>
```
