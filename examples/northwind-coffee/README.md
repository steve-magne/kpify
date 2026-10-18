# Northwind Coffee — acceptance scenario

A small, synthetic online coffee shop, 2026-01-01 → 2026-06-14. The data is fictional and contains
no personal data. It is built to have known answers and to trip up an agent that skips framing,
profiling or validation.

| File | Grain | Rows |
|---|---|---|
| `data/orders.csv` | one order or refund (with duplicates) | 1,370 |
| `data/order_items.csv` | one order line | 2,920 |
| `data/customers.csv` | one customer | 600 |

The prompt given to the agent is in [`prompt.txt`](prompt.txt).

## Planted traps

| Trap | Where | Correct behavior | Checked by |
|---|---|---|---|
| Data ends 2026-06-14 | `orders.csv` | June flagged as partial; the "drop" is an artifact (daily net revenue ≈ 456 EUR in June vs ≈ 428 in May) | `partial_june` |
| Line grain | `order_items.csv` | Revenue not multiplied by joining orders to lines | value checks |
| 24 exact duplicate order rows | `orders.csv` | Detected, removed, logged | `duplicates_found`, value checks |
| 33 refunds as negative-amount rows (`R…` ids) | `orders.csv` | Gross vs net revenue defined explicitly | `refunds_net_vs_gross` |
| One B2B bulk order, 1,920 EUR (~40× median) | `O00526`, 2026-03-11 | Flagged as an outlier, kept visible | `b2b_outlier_flagged` |
| Promo orders have more lines, by construction | `promo_code` | Higher AOV reported as association, not caused by the promo | `promo_not_causal` |
| 15 orders (~1%) without `customer_id` | `orders.csv` | Excluded from repeat rate, and said so | — |
| No sessions/traffic data | — | Conversion rate marked `BLOCKED` | `conversion_blocked` |
| No benchmark or target supplied | — | None invented; any proposed value labeled a hypothesis with its reasoning | `no_invented_benchmark` |
| — | summary | Every number in the summary comes from `kpi-results.json`, `02-data-profile.md` or `04-analysis.md` | prose numbers check |

Refunds always fall in the same month as the order they reverse, so refund timing is not ambiguous.
Signups are spread over the period and no customer orders before signing up, so acquisition is steady
(60–75 new customers per full month): there is no hidden acquisition story to find.

## Known answers

`expected/kpi-results.json`, produced by [`oracle.py`](oracle.py) from the CSVs with plain SQL. Where
two definitions are defensible (AOV on gross or net revenue; refund rate by count or by value),
both values are accepted.

| Month | Net revenue (EUR) | Orders |
|---|---|---|
| 2026-01 | 10,839.80 | 218 |
| 2026-02 | 11,541.30 | 217 |
| 2026-03 | 14,846.50 | 249 |
| 2026-04 | 12,588.60 | 248 |
| 2026-05 | 13,271.70 | 254 |
| 2026-06 (partial, 14 days) | 6,377.10 | 127 |

Repeat purchase rate over the period: 60.4% of identified customers ordered at least twice.

## Rebuild

```bash
python3 examples/northwind-coffee/generate.py
```

```bash
python3 examples/northwind-coffee/oracle.py
```
