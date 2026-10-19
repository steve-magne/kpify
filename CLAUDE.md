# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

kpify is a Claude Code **plugin** (not an application): a set of Agent Skills that make an agent frame, profile, define, validate, visualize and explain KPIs. There is no build step. The deliverables are Markdown skills under `skills/`; the Python is stdlib-only support code (skill scripts, tests, the example scenario). The roadmap and recorded decisions are in `docs/plans/2026-10-18-mvp-plan.md`.

## Commands

Run all Python through `uv` (locally and in CI), e.g. `uv run --no-project python <file>`. Nothing needs installing.

```bash
uv run --no-project python tests/test_check_run.py   # checker unit tests
uv run --no-project python tests/test_profile.py     # profile.py against the Northwind fixture (each test is a plain script, no pytest)
uv run --no-project python examples/northwind-coffee/oracle.py && git diff --exit-code examples/northwind-coffee/expected   # oracle drift
claude plugin validate .                              # manifest check (CI pins @anthropic-ai/claude-code via npx)
claude --plugin-dir .                                 # load this checkout as the plugin for a session
```

`tests/run_scenario.sh [--baseline] [run-dir]` runs the Northwind scenario headless with `claude -p`, then checks the produced `analysis/` against `examples/northwind-coffee/expected/` via `tests/check_run.py`. It costs tokens, so it is on-demand and never in CI. `UPTO=N` checks stages 0..N only; `--baseline` runs without the plugin to record what a plain agent does (see `tests/baseline.md`).

## Architecture

**Stage pipeline.** `skills/kpify/SKILL.md` is the router: it reads the `Status:` line of each artifact in the user's `analysis/` folder, picks the first stage that is missing or not `complete`, announces it, and hands off. Six stage skills (`frame-analysis` → `profile-data` → `define-kpis` → `validate-metrics` → `choose-visuals` → `explain-findings`) each write one numbered artifact (`01-…` to `06-…`) and each read the earlier ones. Direct entry to a stage is allowed; the skill then records missing upstream artifacts as explicit assumptions. Going back is allowed too, via a `## Revisions` section, never a silent rewrite.

**Shared references live in `skills/kpify/references/`** and are used by the other skills as `${CLAUDE_SKILL_DIR}/../kpify/references/…`:
- `artifact-templates.md` is the single source of truth for artifact headings and KPI fields. `tests/check_run.py` parses it to know which `##` headings and fields a run must contain, so editing a template changes what the checker requires.
- `kpi-definition.md` is the shared vocabulary (metric, KPI, target, grain); the other references cover chart selection and the chart and data-quality checklists.

**Scripts shipped with skills** are deterministic checks the skill tells the agent to run: `skills/profile-data/scripts/profile.py` and `skills/explain-findings/scripts/trace_numbers.py` (verifies every number in the summary traces to `kpi-results.json`, `02-data-profile.md` or `04-analysis.md`). `check_run.py` imports `trace_numbers` directly, so the skill's check is the spec for the test harness.

**Acceptance scenario.** `examples/northwind-coffee/` is a synthetic dataset with planted traps (partial June, duplicates, refunds as negative rows, an outlier, no sessions data, and so on) documented in its README. `generate.py` builds the CSVs; `oracle.py` computes known answers with plain SQL into `expected/kpi-results.json` and `traps.json`. CI fails if `oracle.py` changes the committed expected files, so rerun it and commit the result whenever the data or oracle changes.

## Conventions

- Plugin skills are namespaced `/kpify:<name>`. Each `SKILL.md` has `name` and a `description` that is the trigger, so keep it precise. Reference sibling files with `${CLAUDE_SKILL_DIR}`.
- Skills are rigid procedures with red-flag tables. Their rules are stated in the README's Principles and `skills/kpify/SKILL.md`; keep new skills consistent with them (no unlogged cleaning, no invented targets, `UNVALIDATED`/`BLOCKED` labels).
- Skill changes are tested baseline-first: run the scenario without the skill, record the failures in `tests/baseline.md`, then write the skill to fix them.
- Mark deliberate simplifications with a `ponytail:` comment, as in `tests/run_scenario.sh`.
- Version lives in `.claude-plugin/plugin.json` (and the marketplace manifest); the repo is pre-release 0.0.1.
