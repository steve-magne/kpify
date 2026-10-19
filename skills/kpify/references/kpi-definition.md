# KPI definition

## Vocabulary

| Term | Is | Example |
|---|---|---|
| **Measure** | A raw numeric column | `orders.amount` |
| **Metric** | A defined calculation over measures | Net revenue = sum of amount, refunds included |
| **KPI** | A metric chosen because it tracks progress on the decision in the brief | Monthly net revenue, for "is the shop growing?" |
| **Target** | A value the KPI should reach, set by someone accountable | Net revenue ≥ 20k EUR/month (supplied by the owner) |
| **Dimension** | An attribute to slice by | Month, channel, country |
| **Grain** | What one row represents | One order; one order line; one customer-day |

Every KPI is a metric; most metrics are not KPIs. A KPI without a decision is a vanity metric.

## Required fields

A KPI is *defined* only when every field in the `03-kpi-catalog.md` template is filled. The ones
that most often go wrong:

- **Numerator and denominator.** Ratios state both. "Conversion rate" with no sessions data has
  no denominator → `BLOCKED`, not estimated.
- **Grain and aggregation.** Sum at the wrong grain double counts (order total summed over order
  lines). Average of averages is wrong unless weights are equal.
- **Time window.** Calendar month, rolling 30 days, or to-date. Partial periods are flagged,
  never compared raw to full ones.
- **Baseline.** What the value is compared with: prior period, same period last year, a segment.
- **Filters.** Test orders, internal users, refunds, cancelled rows: in or out, and why.

## Variants and ids

When a metric has defensible variants (gross vs net revenue, AOV on gross or net, refund rate by
count or by value), pick one per KPI id and say which in its Formula. Need both? Two ids
(`gross_revenue`, `net_revenue`). From then on, tables, charts and prose name the id, never a
loose label like "revenue".

## Owner

The person accountable for the KPI, as named by the user. Nobody named → `unassigned — not
supplied`. Never invent an owner or infer one from a job title.

## Targets and benchmarks

Never invent a target or an industry benchmark. If the user supplied one, quote it and its
source. Otherwise write `none supplied`, or `hypothesis: <value> — <reasoning>` when proposing.

## Status

- `defined` — computable from available data with the definition above.
- `BLOCKED: <reason>` — a required input is missing. Say what data would unblock it.
