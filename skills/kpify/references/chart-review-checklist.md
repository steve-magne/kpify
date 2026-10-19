# Chart review checklist

Run on every chart before showing it. Record the result in `05-visualization-review.md`.

## Traceability
- [ ] Answers one named question from `01-analysis-brief.md`.
- [ ] Every plotted value traces to a KPI id and a row in `kpi-results.json`.
- [ ] Values in the chart match the results (spot-check at least two points).

## Encoding
- [ ] Chart type matches the question (`chart-selection.md`).
- [ ] Bar charts start at zero. Any non-zero line axis is stated.
- [ ] Categories sorted meaningfully (by value, or natural order such as time).
- [ ] Partial periods visually marked or excluded, and said so.

## Labels
- [ ] Title states the finding or the question, not just the metric name.
- [ ] Axes labeled with units; time grain explicit.
- [ ] Denominator and comparison period stated where relevant.
- [ ] Source and date of data in a footnote.

## Accessibility
- [ ] Readable without color (labels, patterns, or direct annotation).
- [ ] Color-blind-safe palette; text contrast sufficient; labels readable at final size.

## Honesty
- [ ] Annotations claim only what the evidence supports.
- [ ] Outliers shown or their exclusion stated.
- [ ] No chart implies causation the analysis did not establish.
