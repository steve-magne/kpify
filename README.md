<div align="center">

# kpify

### Turn your agent into a BI analyst you can trust.

**Numbers you can trace, KPIs with a definition, charts that don't lie.**

[![Version](https://img.shields.io/badge/version-0.1.0-2563eb)](CHANGELOG.md)
[![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-d97757)](https://code.claude.com/docs/en/plugins)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-7-10b981)](skills/)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

[Quick start](#-quick-start) · [Why kpify](#-the-problem) · [How it works](#-how-it-works) · [Skills](#-the-skills) · [Proof](#-see-it-on-a-dataset-full-of-traps) · [Principles](#-principles)

</div>

---

> *"Revenue dropped in June. What happened?"*
>
> A plain agent answers in two minutes, with confidence. Some of its numbers came from before the
> data was cleaned, the definition of "revenue" changed between the table and the advice, and a
> benchmark appeared from nowhere. **It looks right. You can't tell what isn't.**
>
> kpify makes the agent show its work: every KPI defined, every number traced, every caveat written down.

## ⚡ Quick start

**1. Install** (inside Claude Code):

```text
/plugin marketplace add steve-magne/kpify
/plugin install kpify@kpify
```

**2. Ask a data question** in a project that holds your data:

```text
Why did revenue drop in June?
```

That's it. kpify takes over, starts from the business question, and writes each step to `.kpify/`.
Run `/kpify:kpify` at any time to see where the analysis stands and what comes next.

No API key, no hosted service, no new dependency: the agent uses the data tools your project
already has (SQL, pandas, Polars, DuckDB…).

## 🎯 The problem

We [ran a plain agent](tests/baseline.md) on a small coffee-shop dataset. It caught the obvious
traps: duplicates, refunds, a partial month. Then it wrote the answer, and that's where it broke:

| What the agent wrote | What was true | Failure |
|---|---|---|
| "June: 6,133 EUR" | That's the raw sum *with* duplicates | Number from before cleaning |
| "22 of the 30 duplicates are in May" | 11 | Unverified claim |
| Table says *gross* revenue, advice says *net* | Two different KPIs | Definition drift |
| "Aim for 1.5–3% conversion" | No source | Invented benchmark |
| "Acquisition is collapsing" | Never tested | Hypothesis stated as fact |

**The calculations were fine. The story around them wasn't.** In BI, that's the part that reaches
the decision-maker.

## ✅ What kpify changes

<table>
<tr><th>Without kpify</th><th>With kpify</th></tr>
<tr><td>

- Jumps straight to a chart
- "Revenue" means whatever fits the sentence
- Numbers in prose nobody computed
- Benchmarks and targets made up
- Correlation sold as cause
- One chat answer, gone tomorrow

</td><td>

- Starts from **who decides what**
- Each KPI has a **formula, grain, filters, owner**
- Every number in the summary is **checked by a script** against the results
- Missing targets stay missing, or are labeled **hypothesis**
- Causal claims need evidence, or go to *"What the data cannot tell us"*
- Six **inspectable, versionable** Markdown artifacts

</td></tr>
</table>

## 🔄 How it works

Six stages, adapted from CRISP-DM. Each one writes an artifact, reads the earlier ones, and must
pass a deterministic gate before the next one starts.

```mermaid
flowchart LR
    Q([Business question]) --> F[0 · Frame]
    F --> P[1 · Profile]
    P --> D[2 · Define]
    D --> V[3 · Validate]
    V --> C[4 · Visualize]
    C --> E[5 · Explain]
    E --> R([Decision-ready summary])
    V -. definition or data issue .-> D
    D -. data gap .-> P
```

It's iterative, not waterfall: a later stage can send you back, and the reason is recorded in a
`## Revisions` section, never as a silent rewrite.

```text
.kpify/
├── 01-analysis-brief.md        who decides what, with which questions
├── 02-data-profile.md          keys, joins, duplicates, nulls, outliers, lineage
├── 03-kpi-catalog.md           every KPI: formula, grain, filters, target, owner
├── 04-analysis.md              calculations + reconciliation checks
├── kpi-results.json            the single source of every number
├── charts/                     one chart per question
├── 05-visualization-review.md  each chart against a checklist
└── 06-executive-summary.md     answer first, then evidence, caveats, next actions
```

## 🧰 The skills

| Stage | Skill | Use it when | Writes |
|---|---|---|---|
| — | `/kpify:kpify` | Any time: shows where you are, runs the next stage | — |
| 0 · Frame | `/kpify:frame-analysis` | Starting any analysis | `01-analysis-brief.md` |
| 1 · Profile | `/kpify:profile-data` | New or changed data, or a number looks wrong | `02-data-profile.md` |
| 2 · Define | `/kpify:define-kpis` | Before computing anything | `03-kpi-catalog.md` |
| 3 · Validate | `/kpify:validate-metrics` | Before any chart or conclusion | `04-analysis.md`, `kpi-results.json` |
| 4 · Visualize | `/kpify:choose-visuals` | A chart or dashboard is needed or needs review | `charts/`, `05-visualization-review.md` |
| 5 · Explain | `/kpify:explain-findings` | Reporting results or recommending next steps | `06-executive-summary.md` |

You don't need to call them by name: describe what you want and the right skill triggers.
You can also enter at any stage; missing upstream work is recorded as an explicit assumption.

<details>
<summary><b>Find the skill by what you need</b></summary>

| I want to… | Skill | What you get |
|---|---|---|
| Check that my JSON/CSV files relate and hold together | `profile-data` | Keys, joins (also between differently named ids), orphans, cardinality |
| Find data errors and inconsistencies | `profile-data` → `validate-metrics` | Duplicates, nulls, outliers, partial periods; totals reconciled against the source |
| Find other data worth fetching from the source APIs | `profile-data` | `## Lineage`: producing code, dropped fields, other endpoints (confirmed or hypothesis) |
| Get a relational schema with each table's source | `profile-data` | Mermaid diagram; interactive `.kpify/schema.html` if [Archify](https://github.com/tt-a1i/archify) is installed |
| Decide which KPIs to show | `frame-analysis` → `define-kpis` | KPIs tied to a decision, with definitions and owners |
| Get clear, impactful visuals | `choose-visuals` | One chart per question, values read from `kpi-results.json`, checklist review |
| Explain what the numbers say | `explain-findings` | Short answer first; each finding with evidence, confidence and next action |

</details>

<details>
<summary><b>What a finding looks like</b></summary>

Every finding in `06-executive-summary.md` follows the same shape:

```markdown
### June revenue did not drop
- Observation: June net revenue is about half of May's.
- Evidence: data ends 2026-06-14; daily net revenue ≈ 456 EUR in June vs ≈ 428 in May (04-analysis.md)
- Interpretation: the "drop" is a partial month, not a decline.
- Confidence and caveats: high; 14 days of June only.
- Next action: compare full months, or month-to-date against month-to-date.
```

…followed by `## What the data cannot tell us`: blocked KPIs, open questions, causal claims the data
doesn't support.

</details>

## 🧪 See it on a dataset full of traps

[`examples/northwind-coffee/`](examples/northwind-coffee/) is a synthetic coffee shop with known
answers, computed by plain SQL, and ten planted traps:

`partial month` · `line-grain join` · `24 duplicate rows` · `refunds as negative rows` ·
`a 1,920 EUR B2B outlier` · `promo selection bias` · `orders without customer` ·
`no traffic data for conversion` · `no target supplied` · `numbers in prose`

A test harness runs the whole pipeline headless and checks the `.kpify/` folder against the oracle,
with the same checks the skills run on themselves. Try it on your machine:

```bash
tests/run_scenario.sh
```

> [!NOTE]
> The scenario calls `claude -p` and costs tokens. Add `--baseline` to see what an agent does
> *without* kpify.

## 🧭 Principles

1. **Business question** before chart.
2. **Definitions** before calculations.
3. **Profile** before trusting.
4. **Validate** before visualizing.
5. **Evidence** before interpretation.
6. **Reproducibility** before polish.
7. **Honest uncertainty** over false precision.
8. **Ask** only when the answer materially affects the analysis.
9. **Never silently invent** definitions, targets, missing values, or causal explanations.
10. **Every major output is inspectable** and traceable to its source.

When something can't be computed honestly, kpify says so: a KPI is `UNVALIDATED` until its checks
pass, and `BLOCKED` when the data to compute it doesn't exist.
More in the [methodology](docs/methodology.md).

## ❓ FAQ

<details>
<summary><b>Does my data leave my machine?</b></summary>

No more than it already does with your agent. kpify is Markdown instructions and a few stdlib Python
scripts; there is no service behind it.
</details>

<details>
<summary><b>Do I have to run all six stages?</b></summary>

No. Call any stage directly. kpify notes what it had to assume because earlier artifacts were missing.
</details>

<details>
<summary><b>Will it bury me in questions?</b></summary>

It asks only when the answer materially changes the analysis. Otherwise it records an assumption and
carries on, so you can review it later in the artifacts.
</details>

<details>
<summary><b>Which tools and formats does it work with?</b></summary>

CSV, JSON (including paginated API dumps), and whatever your project already uses to query data.
kpify doesn't install a stack; it tells the agent how to work.
</details>

## 🛠️ Hack on kpify

```bash
claude --plugin-dir /path/to/kpify
```

Skills are tested baseline-first: record what a plain agent gets wrong, then write the skill that
fixes it. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [changelog](CHANGELOG.md).

## 🙏 Credits

Ideas (not code or text; see [NOTICE](NOTICE)) borrowed from
[obra/superpowers](https://github.com/obra/superpowers) (MIT) for workflow discipline and
baseline-first skill testing, [pbakaus/impeccable](https://github.com/pbakaus/impeccable)
(Apache-2.0) for a domain command vocabulary backed by shared references, and
[morluto/rea](https://github.com/morluto/rea) (MIT) for evidence-first investigation.

## License

[MIT](LICENSE)

<div align="center">

**If kpify saved you from a wrong number in a meeting, ⭐ the repo.**

</div>
