---
name: frame-analysis
description: Use at the start of any data analysis, KPI or dashboard request, before profiling or calculating anything — and whenever the business question, audience or scope changes. Pins down the decision the analysis supports, who reads it, the specific questions, scope and known definitions, and writes analysis/01-analysis-brief.md. Asks the user only questions whose answer would change a KPI or a conclusion.
---

# frame-analysis — stage 0

Understand the decision before touching the numbers. Output: `analysis/01-analysis-brief.md`,
following `${CLAUDE_SKILL_DIR}/../kpify/references/artifact-templates.md`.

## Procedure

1. **Read the request literally.** Write down the decision or action behind it. "Revenue dropped,
   what happened?" → the owner must decide whether to act on a drop, and how.
2. **Look at what data exists, without analyzing it.** List files and tables, their names and
   sizes, the columns' names. Do not compute values yet: that is stage 1, and early numbers
   anchor the framing.
3. **Fill the brief.** Decision, audience, questions, scope, known definitions, data available.
   - Questions are specific and answerable: "Did net revenue per day fall in June vs May?",
     not "Analyze revenue".
   - Quote any definition, target or threshold the user gave, verbatim. Do not add your own.
   - If the user asked for something the data cannot provide (a rate with no denominator),
     keep the question and note the gap under Data available. Stage 2 will mark it `BLOCKED`.
4. **Decide what to ask.** For each open point, ask: *would a different answer change which
   KPI we compute, how, or what we conclude?*
   - Yes → ask. At most 3 questions, in one message, each with the assumption you will use if
     there is no answer.
   - No → write it as an assumption and move on.
   - The user is unavailable (said so, or headless run) → write every open point as an
     assumption, with what would change if it is wrong.
5. **Set `Status: complete`** once the gate below passes, then return to `kpify:kpify`.

Typical questions worth asking: gross or net (refunds, cancellations, taxes)? Which timezone or
fiscal calendar? What counts as an active customer? Is there a target, and who set it?
Not worth asking: chart colors, file names, anything you can find in the data.

## Gate

- [ ] Headings exactly as in the template: `## Decision`, `## Audience`, `## Questions`,
      `## Scope`, `## Known definitions`, `## Data available`, `## Open questions`,
      `## Assumptions`, `## Revisions` (write "None." under an empty one).
- [ ] Decision and audience stated in the user's terms.
- [ ] Every question is specific enough that a number could answer it.
- [ ] Scope has a period, a granularity and an entity.
- [ ] Every user-supplied definition or target is quoted, and nothing else is presented as one.
- [ ] Every open point is either asked or recorded as an assumption, with its impact.
- [ ] No values computed from the data yet.

## Language

Artifact headings stay exactly as in the template (the checker reads them). Write the content in
the user's language.

## Red flags

| Thought | Reality |
|---|---|
| "The question is obvious, skip the brief" | The brief takes two minutes and is what later stages check against. |
| "Let me just peek at the totals first" | Totals before framing anchor the question on the first number seen. |
| "I'll ask everything to be safe" | Each question costs the user time. Ask only what changes the analysis. |
| "They want conversion rate, I'll estimate traffic" | Keep the question; record the missing data. Never invent a denominator. |
