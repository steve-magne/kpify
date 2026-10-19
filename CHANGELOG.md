# Changelog

## 0.1.0 — unreleased

First release: the `kpify` router and six stage skills, with an acceptance scenario that checks them.

### Added
- Skills: `kpify` (router), `frame-analysis`, `profile-data`, `define-kpis`, `validate-metrics`,
  `choose-visuals`, `explain-findings`, with shared references in `skills/kpify/references/`.
- Northwind Coffee scenario with seeded data, an oracle for the known answers, and trap checks
  (`tests/check_run.py`, `tests/run_scenario.sh`); baseline without the plugin in `tests/baseline.md`.
- CI: self-tests, oracle drift check, plugin validation.
- `docs/methodology.md`, `CONTRIBUTING.md`, `NOTICE`.

### Verification
- Full scenario run (`tests/run_scenario.sh`, stages 0–5): **result pending** — to be filled in before the tag.
- Clean install from the marketplace (`/plugin marketplace add steve-magne/kpify`, `/plugin install kpify@kpify`) checked in an isolated config on 2026-10-19.
- Credits: no passage shared with obra/superpowers, pbakaus/impeccable or morluto/rea beyond generic boilerplate.
