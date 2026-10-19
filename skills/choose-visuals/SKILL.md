---
name: choose-visuals
description: Use after KPIs are validated and before presenting any chart, graph or dashboard — or whenever a chart is requested or needs review. Picks each chart from the question it answers, plots only values read from .kpify/kpi-results.json, marks partial periods, writes the chart files locally to .kpify/charts/ and reviews every one against the chart checklist in .kpify/05-visualization-review.md.
allowed-tools: Bash(python3 *), Bash(uv *)
---

# choose-visuals — stage 4

Chart only what answers a question, and only what was validated. Outputs: chart files in
`.kpify/charts/`, their code, and `.kpify/05-visualization-review.md`, following
`${CLAUDE_SKILL_DIR}/../kpify/references/artifact-templates.md`. Pick charts with
`${CLAUDE_SKILL_DIR}/../kpify/references/chart-selection.md`; review them with
`${CLAUDE_SKILL_DIR}/../kpify/references/chart-review-checklist.md`.

## Procedure

1. **Read the brief, the catalog and the results** (`01-analysis-brief.md`, `03-kpi-catalog.md`,
   `04-analysis.md`, `kpi-results.json`). Each missing one → record `Assumed (no <file>): …`.
   No `kpi-results.json` → there is nothing validated to chart; go back to
   `kpify:validate-metrics`, or label every chart `UNVALIDATED` in its title.
2. **List the charts.** One per question in the brief that a picture answers better than a
   number; often two to four. A question answered by one value or a short table gets a table in
   the summary, not a chart. For each: the question, the KPI ids, the chart type from
   `chart-selection.md` and why.
3. **Write one script that draws them all**, e.g. `.kpify/charts.py`, and run it. It:
   - reads every plotted value from `kpi-results.json` by `id`, `period` and `segment` — no
     number typed into the code, no recomputation;
   - plots only `validated` rows; an `unvalidated` series says so in its title, a `blocked` KPI
     is not plotted;
   - marks a partial period (rows with a `note`) with a hatch, a dashed segment or by excluding
     it, and says which in a label on the chart; compares it per day, not as a raw total;
   - writes each chart to `.kpify/charts/<name>.png` (or `.svg`, or self-contained `.html`).
     Use what the project has (matplotlib, plotly…). Nothing installed →
     `uv run --with matplotlib python .kpify/charts.py`, or write the SVG with the stdlib.
   - Files on disk are the deliverable. Never stop at an online artifact or an inline chart: if
     you also publish one, do it after the files exist.
4. **Label for a reader who skipped the analysis.** Title states the question or the finding;
   axes have units and time grain; a footnote gives the source (`kpi-results.json`, KPI ids) and
   the data range. Bars start at zero. No dual axes, no pie beyond three parts, no 3D.
5. **Review every chart** against the whole checklist. Open each file and look at it. Spot-check
   two plotted points against `kpi-results.json`. Fix and redraw failures; record the result.
6. **Write `05-visualization-review.md`**: one `## Chart:` block per file, the file name exactly
   as in `charts/`:

   ```markdown
   ## Chart: net-revenue-per-day.png

   - Question: Q1 — did revenue really drop in June?
   - KPI ids: net_revenue_per_day
   - Chart type and why: line — change over time; June dashed, partial (14/30 days)
   - Checklist: pass (spot-checked 2026-05 and 2026-06 against kpi-results.json)
   ```

   Then `## Assumptions` and `## Revisions`.
7. **Revisit upstream if needed.** A chart that needs a number not in `kpi-results.json` sends
   you back to `kpify:validate-metrics` to add it to the code (`## Revisions` there).
8. **Set `Status: complete`** once the gate passes, then return to `kpify:kpify`.

## Gate

- [ ] `python3 ${CLAUDE_SKILL_DIR}/../kpify/scripts/check_artifacts.py .kpify --stage 4` prints 0 failures
      (one `## Chart: <file>` block per file in `charts/` and no block without its file,
      `## Assumptions` and `## Revisions` not empty). Fix every FAIL line and rerun.
- [ ] Each chart names one question from the brief and the KPI ids it plots.
- [ ] The chart code reads its values from `kpi-results.json`; it reruns and redraws the files.
- [ ] Every checklist item passed, or its failure is recorded with the fix.
- [ ] Partial periods are marked or excluded on every chart that covers them, and the chart says so.
- [ ] No annotation or title claims a cause the analysis did not establish.

## Red flags

| Thought | Reality |
|---|---|
| "I'll publish the chart as an artifact" | Publishing needs approval and may not happen. Write the file to `.kpify/charts/` first. |
| "I'll type the values from the results table" | Typed values drift. The code reads `kpi-results.json`. |
| "June is just lower, plot it as is" | A raw partial month looks like a drop. Per day, and marked. |
| "A dashboard of every KPI" | A chart that answers no question is noise. One question per chart. |
| "Promo vs no-promo bars, titled 'Promo lifts AOV'" | An association. Title it as one. |
| "Two measures, one chart, two axes" | Two aligned charts. Dual axes invite false comparisons. |
| "Looks fine in the code" | Open the file. Check two points against the results. |
