# kpify

**BI skills for reliable metrics and decision-ready visuals.**

kpify is a set of [Agent Skills](https://code.claude.com/docs/en/skills) that makes an AI
coding agent work like a careful BI analyst: frame the business question, profile the data,
define KPIs, validate the calculations, choose honest charts, and report findings with their
evidence and caveats. Every stage writes an inspectable artifact to `.kpify/`.

> **Status: 0.1.0.** The `kpify` router and six stage skills (`frame-analysis`, `profile-data`,
> `define-kpis`, `validate-metrics`, `choose-visuals`, `explain-findings`). See the
> [changelog](CHANGELOG.md) and the [methodology](docs/methodology.md).

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

| Stage | Skill | When | Artifact |
|---|---|---|---|
| — | `/kpify:kpify` | Any time: shows where the analysis stands and runs the next stage | — |
| 0 Frame | `/kpify:frame-analysis` | Start of any analysis: who decides what, with which questions | `.kpify/01-analysis-brief.md` |
| 1 Profile | `/kpify:profile-data` | New or changed data, or a number looks wrong | `.kpify/02-data-profile.md` |
| 2 Define | `/kpify:define-kpis` | Before computing anything: exact formula, grain, filters, target | `.kpify/03-kpi-catalog.md` |
| 3 Validate | `/kpify:validate-metrics` | Before any chart or conclusion, or after a definition or data change | `.kpify/04-analysis.md`, `kpi-results.json`, code |
| 4 Visualize | `/kpify:choose-visuals` | A chart or dashboard is needed or needs review | `.kpify/charts/`, `.kpify/05-visualization-review.md` |
| 5 Explain | `/kpify:explain-findings` | Reporting results, explaining a change, recommending next steps | `.kpify/06-executive-summary.md` |

### By need

| I want to… | Skill | What you get |
|---|---|---|
| Check that my JSON/CSV files relate and hold together | `/kpify:profile-data` | Keys, joins (also between differently named ids), orphans, cardinality |
| Find data errors and inconsistencies | `/kpify:profile-data`, then `/kpify:validate-metrics` | Duplicates, nulls, outliers, partial periods; totals reconciled against the source |
| Find other data worth fetching from the source APIs | `/kpify:profile-data` | `## Lineage`: producing code, dropped fields, other endpoints (confirmed or hypothesis) |
| Get a relational schema with each table's source | `/kpify:profile-data` | Mermaid diagram; interactive `.kpify/schema.html` if [Archify](https://github.com/tt-a1i/archify) is installed |
| Decide which KPIs to show | `/kpify:frame-analysis`, then `/kpify:define-kpis` | KPIs tied to a decision, with definitions and owners |
| Get clear, impactful visuals | `/kpify:choose-visuals` | One chart per question, values read from `kpi-results.json`, checklist review |
| Explain what the numbers say | `/kpify:explain-findings` | Short answer first, each finding with evidence, confidence and next action |

Each stage reads the artifacts of the earlier ones; running one out of order records what it had
to assume.

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

Ideas (not code or text; see [NOTICE](NOTICE)) borrowed from [obra/superpowers](https://github.com/obra/superpowers)
(MIT) for workflow discipline and baseline-first skill testing,
[pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache-2.0) for a domain command
vocabulary backed by shared references, and [morluto/rea](https://github.com/morluto/rea) (MIT)
for evidence-first investigation.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add or change a skill.

## License

[MIT](LICENSE)
