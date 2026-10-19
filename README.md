# kpify

**BI skills for reliable metrics and decision-ready visuals.**

kpify is a set of [Agent Skills](https://code.claude.com/docs/en/skills) that makes an AI
coding agent work like a careful BI analyst: frame the business question, profile the data,
define KPIs, validate the calculations, choose honest charts, and report findings with their
evidence and caveats. Every stage writes an inspectable artifact to `analysis/`.

> **Status: pre-release (0.0.1).** The `kpify` router and stages 0–3 (`frame-analysis`, `profile-data`,
> `define-kpis`, `validate-metrics`) exist.
> The remaining stage skills land in the next increments — see [the MVP plan](docs/plans/2026-10-18-mvp-plan.md).

## Install (Claude Code)

From inside Claude Code:

```text
/plugin marketplace add steve-magne/kpify
/plugin install kpify@kpify
```

Or from a shell:

```bash
claude plugin marketplace add steve-magne/kpify
```

```bash
claude plugin install kpify@kpify
```

To hack on kpify itself, load your checkout for one session instead:

```bash
claude --plugin-dir /path/to/kpify
```

No API key or hosted service is needed. The agent uses whatever data tools your project
already has (SQL, Python with pandas/Polars, DuckDB…).

## Use

Ask a data question in a project that contains your data files:

```text
Explore these CSVs and tell me what is worth measuring.
Why did revenue drop in June?
```

kpify starts with the business question, not the chart. Run `/kpify:kpify` at any time to see
where the analysis stands and what comes next.

## Workflow

Adapted from CRISP-DM, iterative rather than waterfall: a later stage may send you back to an
earlier one, and the reason is recorded.

| Stage | Skill | Artifact |
|---|---|---|
| 0 Frame | `frame-analysis` | `analysis/01-analysis-brief.md` |
| 1 Profile | `profile-data` | `analysis/02-data-profile.md` |
| 2 Define | `define-kpis` | `analysis/03-kpi-catalog.md` |
| 3 Validate | `validate-metrics` | `analysis/04-analysis.md`, `kpi-results.json`, code |
| 4 Visualize | `choose-visuals` | `analysis/charts/`, `analysis/05-visualization-review.md` |
| 5 Explain | `explain-findings` | `analysis/06-executive-summary.md` |

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

## Credits

Ideas (not code or text) borrowed from [obra/superpowers](https://github.com/obra/superpowers)
(MIT) for workflow discipline and baseline-first skill testing,
[pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache-2.0) for a domain command
vocabulary backed by shared references, and [morluto/rea](https://github.com/morluto/rea) (MIT)
for evidence-first investigation.

## License

[MIT](LICENSE)
