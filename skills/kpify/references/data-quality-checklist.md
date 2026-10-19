# Data quality checklist

Run every item against every source. Record each finding in `02-data-profile.md` → Quality
issues, with a count and an example row. Never fix silently.

## Structure
- [ ] Row count and column count match expectations (file not truncated, header row correct).
- [ ] Types parse: dates are dates, numbers are numbers, no numbers stored as text.
- [ ] Grain stated: what one row represents. Check that the candidate key is unique.

## Completeness
- [ ] Null / blank rate per column. Distinguish null, empty string, `0`, `"N/A"`.
- [ ] Date coverage: first and last date, gaps. **Is the last period complete?**
- [ ] Expected segments present (all months, all regions).

## Uniqueness
- [ ] Exact duplicate rows.
- [ ] Duplicate keys with differing values (which row wins, and why?).

## Validity
- [ ] Ranges: negative amounts (refunds? errors?), future dates, impossible values.
- [ ] Units and currencies consistent within a column (cents vs units, EUR vs USD).
- [ ] Categorical values: spelling variants, case, trailing spaces.

## Consistency across sources
- [ ] Foreign keys resolve (orphans counted).
- [ ] Join cardinality as expected; joining does not multiply rows unexpectedly.
- [ ] Totals reconcile across sources (sum of lines = order total).

## Distribution
- [ ] Outliers: values far from the median. Investigate before deciding; keep them visible.
- [ ] Skew: is the mean meaningful, or report the median too?

## Bias and leakage
- [ ] Is the sample the population? (Survivorship, opt-in, filtered exports.)
- [ ] Do any columns encode the outcome (status set after the fact)?

## Sensitive data
- [ ] Personal data (names, emails, addresses, IDs) identified. Do not copy it into artifacts;
      aggregate or pseudonymise.
- [ ] No secrets (keys, tokens, connection strings) in artifacts or code.
