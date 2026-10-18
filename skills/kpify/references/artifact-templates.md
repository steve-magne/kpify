# Artifact templates

Every artifact lives in `analysis/` and starts with the same header. Headings marked
*(required)* are checked by `tests/check_run.py`; keep their exact text.

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
## Decision (required)
<The decision or action this analysis informs. One or two sentences.>

## Audience (required)
<Who reads the result and what they can act on.>

## Questions (required)
1. <Specific question the data must answer>

## Scope (required)
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

```markdown
## Sources (required)
| Source | Rows | Columns | Grain (one row = …) | Date range | Key |
|---|---|---|---|---|---|

## Columns (required)
| Source.column | Type | Role (id / dimension / measure / date) | Nulls % | Distinct | Notes |
|---|---|---|---|---|---|

## Relationships (required)
<Join keys, cardinality (1:1, 1:N), orphans found.>

## Quality issues (required)
| # | Issue | Evidence (count, example) | Impact | Handling |
|---|---|---|---|---|

Handling is one of: `open`, `transformed (see below)`, `accepted (reason)`.

## Transformations (required)
| # | Transformation | Rows affected | Reason | Reversible? |
|---|---|---|---|---|

## Observations vs hypotheses
- Observed: <fact with count>
- Hypothesis: <possible explanation, not yet tested>
```

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
| Owner | |
| Confidence | high / medium / low — <why> |
| Status | defined / BLOCKED: <reason> |
```

## 04-analysis.md

```markdown
## Code (required)
<Path(s) to the SQL / Python that computes every KPI, and the command to rerun it.>

## Results (required)
| KPI id | Period | Segment | Value | Unit | Status |
|---|---|---|---|---|---|

## Validation checks (required)
| # | KPI id | Check | Expected | Actual | Pass? |
|---|---|---|---|---|---|

## Findings (required)
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
   "value": 12345.67, "unit": "EUR", "status": "validated"}
]
```

`status` is one of `validated`, `unvalidated`, `blocked` (`value` is `null` when blocked).

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
## Summary (required)
<Three sentences or fewer: the answer to the brief's questions.>

## Findings (required)

### <Finding title>
- Observation:
- Evidence: <value, comparison, period, segment; link to 04-analysis.md row or chart>
- Interpretation:
- Confidence and caveats:
- Next action:

## What the data cannot tell us
<Questions left open, blocked KPIs, causal claims not supported.>
```
