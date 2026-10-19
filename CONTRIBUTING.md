# Contributing

Skills live in `skills/<name>/SKILL.md`. The `description` line is the trigger and the most important
line in the file. Shared material lives once in `skills/kpify/references/`. Repo docs and skills are in
English. Python in tests is stdlib only and runs through `uv`.

## Adding or changing a skill

Test a skill the way it will be used: against a scenario with known answers, starting from what the agent
does **without** it.

1. **Run the baseline first.** Run the scenario without the plugin and record what a plain agent gets
   right and wrong in [`tests/baseline.md`](tests/baseline.md). Only the failures justify new skill text.

   ```bash
   tests/run_scenario.sh --baseline
   ```

2. **Add a trap** for the failure you want to fix to
   [`examples/northwind-coffee/expected/traps.json`](examples/northwind-coffee/expected/traps.json):
   an `id`, the artifact `files` to look in, and `patterns` that must match, or a `forbid` regex with an
   `unless` escape. If the trap needs planted data, change `generate.py` and describe it in the scenario
   README.

3. **Add the expected value through the oracle.** Never edit `expected/kpi-results.json` by hand. Add the
   KPI to [`oracle.py`](examples/northwind-coffee/oracle.py), which computes it from the CSVs in plain SQL,
   then regenerate (CI fails on drift):

   ```bash
   uv run --no-project python examples/northwind-coffee/generate.py
   ```

   ```bash
   uv run --no-project python examples/northwind-coffee/oracle.py
   ```

4. **Write or change the skill** so the failure goes away. Prefer a gate or a checklist to prose advice,
   and point to `references/` instead of repeating it. If a skill's output format changes, update
   `artifact-templates.md`: `check_run.py` reads its required headings and KPI fields from there.

5. **Run the checks.** The self-tests are free:

   ```bash
   uv run --no-project python tests/test_check_run.py
   ```

   ```bash
   uv run --no-project python tests/test_profile.py
   ```

   ```bash
   claude plugin validate .
   ```

   Then the full scenario, which costs tokens. `UPTO=N` stops the check after stage N:

   ```bash
   tests/run_scenario.sh
   ```

6. **Record what changed**: a line in [`CHANGELOG.md`](CHANGELOG.md) and, when the baseline moved,
   an update to `tests/baseline.md`. A skill change that the scenario does not exercise should say so.

## Credits

If an idea comes from another project, say so in [`NOTICE`](NOTICE). Do not copy code or text from it
without checking its license and adding the required notice.
