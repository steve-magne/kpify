---
name: profile-data
description: Use after the analysis is framed and before defining or computing any KPI — or whenever new data arrives or a number looks wrong. Inventories every source (files or SQL tables), establishes the grain, keys, joins and date coverage, and records data-quality issues (duplicates, nulls, negative or outlier values, incomplete periods, unit mismatches) in analysis/02-data-profile.md without silently cleaning anything.
allowed-tools: Bash(python3 *)
---

# profile-data — stage 1

Establish what the data contains and how far to trust it. Output: `analysis/02-data-profile.md`,
following `${CLAUDE_SKILL_DIR}/../kpify/references/artifact-templates.md`. Work through
`${CLAUDE_SKILL_DIR}/../kpify/references/data-quality-checklist.md` for every source.

## Procedure

1. **Read the brief** (`analysis/01-analysis-brief.md`). Profile what the questions need first;
   note anything else in passing. No brief → record `Assumed (no 01-analysis-brief.md): …`.
2. **Run the deterministic profile.** For CSV/TSV/JSON/JSONL files (nested JSON is flattened:
   dotted columns, child tables for lists of objects):

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/profile.py <files...>
   ```

   For SQL databases, run the equivalent queries (row counts, `COUNT(DISTINCT key)`, null
   counts, `MIN`/`MAX` of dates and measures, duplicate keys) and keep the SQL in
   `analysis/profile.sql`. For Excel or Parquet, convert to CSV with whatever the project
   has (DuckDB, pandas) or profile with it directly — and say which tool was used.
   Every count in the artifact must come from this output or a query you ran, never from memory.
   Say what each count counts: "131 rows in June (raw, before dedup)" is not "131 orders".
   Per-period breakdowns of an issue come from the script's "By month" table or a query, never
   from adding up by hand.
3. **Establish the grain** of every source: "one row = one …". Confirm it with the key's
   uniqueness. When it is not unique, find out why (exact duplicates? one row per line item?
   per status change?) before going further.
4. **Trace lineage.** Search the project for the code that produces each source file (HTTP
   calls such as `fetch`, `axios`, `requests`, `httpx`, SDK clients, SQL exports, and the code
   that writes the file). Record in `## Lineage`: file, producing code (`path:line`), endpoint or
   query, fields the response returns but the code drops, and parameters it fixes (date range,
   filters, page size — a missing pagination loop truncates data). Then list **other data worth
   fetching** for the brief's questions: dropped fields first, then other endpoints of the same
   API. An endpoint not seen in the code is a hypothesis until confirmed in the API's docs
   (`ctx7` or the vendor reference); say which. Never copy keys or tokens from that code.
5. **Check joins.** For each relationship the questions need: key, cardinality, orphans on each
   side. A 1:N join under a sum multiplies the "1" side's measures — write that down. The
   script's "Inferred joins" are candidates found by value overlap between differently named
   columns: keep the ones whose meaning you confirmed, reject the rest with the reason.
   Copy the script's Mermaid diagram into `## Relationships`, drop rejected edges, and add one
   node per API endpoint or query feeding each file (`api1["GET /v1/orders"] --> t0`), so the
   diagram shows both the joins and where each table comes from.
   **Interactive schema with [Archify](https://github.com/tt-a1i/archify).** If the `archify`
   skill is available, use it to render `analysis/schema.html` as an `erd` from this diagram and
   `## Lineage`: one entity per table with its profiled columns, `pk` on candidate keys, `fk` +
   `references` on confirmed joins only, `sublabel` = endpoint or query, `sources` = the
   producing code (`path`, `line`), and `tag` = source system, so tables from one API share a
   band. Run its `finalize` gate; a failing receipt is not a deliverable. Not installed → keep
   the Mermaid diagram and tell the user `npx skills add tt-a1i/archify -g` adds it; never
   install it yourself.
6. **Investigate each anomaly enough to describe it**, with a count and one example: duplicates,
   negative values (refunds? corrections?), values far from the median, blanks, partial periods,
   unit or currency mixes, text variants. Keep **observed** (counted) apart from **hypothesis**
   (possible explanation).
7. **Decide handling, do not apply it silently.** Each issue gets `open`, `transformed`, or
   `accepted (reason)`. A transformation is listed in Transformations with the rows affected,
   and is applied later in reproducible code (stage 3), never by editing the source files.
8. **Revisit the brief if needed.** If the data cannot answer a question, or changes its meaning
   (the last period is partial), add a `## Revisions` entry to the brief.
9. **Set `Status: complete`** once the gate passes, then return to `kpify:kpify`.

## Gate

- [ ] Headings exactly as in the template: `## Sources`, `## Columns`, `## Relationships`,
      `## Lineage`, `## Quality issues`, `## Transformations`, `## Observations vs hypotheses`,
      `## Assumptions`, `## Revisions` (write "None." under an empty one).
- [ ] Every source listed with rows, columns, grain, date range and key.
- [ ] Every column has a role: identifier, dimension, measure, date, or unused.
- [ ] Joins needed by the questions checked for cardinality and orphans; inferred joins kept or
      rejected with a reason.
- [ ] `## Relationships` holds a Mermaid diagram of the tables, their joins and their sources,
      and links `schema.html` when Archify rendered it.
- [ ] Every source traced in `## Lineage` (or `unknown origin`), with data worth fetching marked
      confirmed (seen in code or docs) or hypothesis.
- [ ] Every data-quality checklist item checked; each finding has a count and an example.
- [ ] Each issue has a handling decision; no source file was modified.
- [ ] The last period's coverage is stated (complete or `n/N days`).
- [ ] No personal data copied into the artifact beyond what is needed (ids, not names or emails).

## Red flags

| Thought | Reality |
|---|---|
| "I'll drop the duplicates and move on" | Record them first: count, example, decision. Then drop in code. |
| "Negative amounts are errors" | Often refunds or corrections. Find out; they may define net vs gross. |
| "That outlier is noise, exclude it" | It may be the most important row. Flag it, keep it visible, decide in stage 2. |
| "Roughly 20 duplicates, mostly in May" | Counts come from the script or a query, not from memory. |
| "The last month looks low" | Check its coverage before calling it a drop. |
| "The API surely has a churn endpoint" | Unseen in code or docs = hypothesis. Say so. |
| "Same values, so it's a join" | Overlap is a candidate. Confirm the meaning before joining. |
