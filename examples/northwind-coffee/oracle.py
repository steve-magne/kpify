"""Compute the known-correct KPI answers for Northwind Coffee from the CSVs alone (sqlite3, stdlib).

Writes expected/kpi-results.json. Each entry lists every defensible value ("values") for a KPI and
period; tests/check_run.py passes a KPI when the agent reported any one of them.
"""

import csv
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent

SQL_MONTHLY = """
WITH o AS (SELECT DISTINCT * FROM orders),                     -- drop exact duplicate export rows
m AS (
  SELECT substr(order_date, 1, 7) AS period,
         SUM(CASE WHEN amount_eur > 0 THEN amount_eur END)       AS gross,
         -SUM(CASE WHEN amount_eur < 0 THEN amount_eur ELSE 0 END) AS refunded,
         SUM(amount_eur)                                         AS net,
         SUM(amount_eur > 0)                                     AS orders,
         SUM(amount_eur < 0)                                     AS refunds
  FROM o GROUP BY 1
)
SELECT period, gross, refunded, net, orders, refunds FROM m ORDER BY period
"""

SQL_REPEAT = """
WITH c AS (
  SELECT customer_id, COUNT(DISTINCT order_id) AS n
  FROM orders WHERE amount_eur > 0 AND customer_id <> '' GROUP BY 1
)
SELECT SUM(n >= 2) * 1.0 / COUNT(*) FROM c
"""


def load(db, name):
    with open(HERE / "data" / f"{name}.csv", newline="") as f:
        rows = list(csv.reader(f))
    cols = ", ".join(f'"{c}"' for c in rows[0])
    db.execute(f"CREATE TABLE {name} ({cols})")
    db.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(rows[0]))})", rows[1:])


def main():
    db = sqlite3.connect(":memory:")
    for name in ("orders", "order_items", "customers"):
        load(db, name)
    db.execute("CREATE TABLE t AS SELECT order_id, order_date, customer_id, CAST(amount_eur AS REAL) AS amount_eur, promo_code FROM orders")
    db.execute("DROP TABLE orders")
    db.execute("ALTER TABLE t RENAME TO orders")

    expected = []
    for period, gross, refunded, net, orders, refunds in db.execute(SQL_MONTHLY):
        expected += [
            kpi("net_revenue", period, "EUR", net),
            kpi("orders", period, "count", orders),
            kpi("aov", period, "EUR", gross / orders, net / orders),
            kpi("refund_rate", period, "ratio", refunds / orders, refunded / gross),
        ]
    (repeat,) = db.execute(SQL_REPEAT).fetchone()
    expected.append(kpi("repeat_purchase_rate", "total", "ratio", repeat))

    out = HERE / "expected" / "kpi-results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(expected, indent=1) + "\n")

    (dupes,) = db.execute("SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM orders)) FROM orders").fetchone()
    (raw_items,) = db.execute("""SELECT SUM(o.amount_eur) FROM (SELECT DISTINCT * FROM orders) o
                                 JOIN order_items i USING (order_id)""").fetchone()
    print(f"wrote {out.relative_to(HERE)}: {len(expected)} KPI rows")
    print(f"duplicate order rows: {dupes}; line-grain join would inflate gross revenue to {raw_items:.2f}")


def kpi(id, period, unit, *values):
    return {"id": id, "period": period, "unit": unit, "values": [round(v, 4) for v in values]}


if __name__ == "__main__":
    main()
