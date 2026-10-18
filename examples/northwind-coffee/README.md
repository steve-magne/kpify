# Northwind Coffee — acceptance scenario

A small, synthetic online coffee shop, 2026-01-01 → 2026-06-14. The data is fictional and contains
no personal data. It is built to have known answers and to trip up an agent that skips framing,
profiling or validation.

| File | Grain | Rows |
|---|---|---|
| `data/orders.csv` | one order or refund (with duplicates) | 1,423 |
| `data/order_items.csv` | one order line | 2,960 |
| `data/customers.csv` | one customer | 600 |

The prompt given to the agent is in [`prompt.txt`](prompt.txt).

## Planted traps

| Trap | Where | Correct behavior | Checked by |
|---|---|---|---|
| Data ends 2026-06-14 | `orders.csv` | June flagged as partial; the "drop" is mostly an artifact (daily net revenue ≈ 432 EUR in June vs ≈ 449 in May) | `partial_june` |
| Line grain | `order_items.csv` | Revenue not multiplied by joining orders to lines | value checks |
| 30 exact duplicate order rows | `orders.csv` | Detected, removed, logged | `duplicates_found`, value checks |
| 39 refunds as negative-amount rows (`R…` ids) | `orders.csv` | Gross vs net revenue defined explicitly | `refunds_net_vs_gross` |
| One B2B bulk order, 1,920 EUR (~40× median) | `O00556`, 2026-03-11 | Flagged as an outlier, kept visible | `b2b_outlier_flagged` |
| Promo orders have more lines, by construction | `promo_code` | Higher AOV reported as association, not caused by the promo | `promo_not_causal` |
| ~1% orders without `customer_id` | `orders.csv` | Excluded from repeat rate, and said so | — |
| No sessions/traffic data | — | Conversion rate marked `BLOCKED` | `conversion_blocked` |

Refunds always fall in the same month as the order they reverse, so refund timing is not ambiguous.

## Known answers

`expected/kpi-results.json`, produced by [`oracle.py`](oracle.py) from the CSVs with plain SQL. Where
two definitions are defensible (AOV on gross or net revenue; refund rate by count or by value),
both values are accepted.

| Month | Net revenue (EUR) | Orders |
|---|---|---|
| 2026-01 | 11,921.30 | 239 |
| 2026-02 | 12,571.40 | 225 |
| 2026-03 | 14,728.40 | 252 |
| 2026-04 | 12,712.30 | 243 |
| 2026-05 | 13,918.10 | 270 |
| 2026-06 (partial, 14 days) | 6,048.90 | 125 |

Repeat purchase rate over the period: 63.9% of identified customers ordered at least twice.

## Rebuild

```bash
python3 examples/northwind-coffee/generate.py
```

```bash
python3 examples/northwind-coffee/oracle.py
```
