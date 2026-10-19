#!/usr/bin/env bash
# Run the Northwind Coffee scenario headless with Claude Code, then check the result.
# Costs tokens: run on demand, not in CI.
#
#   tests/run_scenario.sh [--baseline] [run-dir]
#
# UPTO=N checks stages 0..N only. --baseline runs without the kpify plugin (to record what a plain agent does) and skips the checker.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SCENARIO=$ROOT/examples/northwind-coffee
PLUGIN=(--plugin-dir "$ROOT")
if [[ ${1:-} == --baseline ]]; then PLUGIN=(); shift; fi
RUN=${1:-$(mktemp -d)}

mkdir -p "$RUN"
cp "$SCENARIO"/data/*.csv "$RUN"/
cd "$RUN"
# ponytail: allowlist covers common local data tools; extend if a run needs another CLI.
claude -p "$(cat "$SCENARIO/prompt.txt")" ${PLUGIN[@]+"${PLUGIN[@]}"} \
  --settings '{"language": "English"}' \
  --permission-mode acceptEdits \
  --allowedTools "Read,Write,Edit,Glob,Grep,Skill,Bash(python3:*),Bash(uv:*),Bash(duckdb:*),Bash(sqlite3:*),Bash(ls:*),Bash(head:*),Bash(wc:*),Bash(mkdir:*)" \
  --max-turns 80 < /dev/null > transcript.md

echo "run dir: $RUN"
if [[ ${#PLUGIN[@]} -gt 0 ]]; then
  python3 "$ROOT/tests/check_run.py" "$RUN/analysis" "$SCENARIO/expected" --upto "${UPTO:-5}"
fi
