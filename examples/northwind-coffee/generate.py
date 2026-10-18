"""Generate the Northwind Coffee fixture: a small online coffee shop, 2026-01-01 to 2026-06-14.

Deterministic (seeded). Stdlib only. Writes data/customers.csv, data/orders.csv, data/order_items.csv.
Planted traps are listed in README.md; expected answers come from oracle.py, not from here.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260614
START, END = date(2026, 1, 1), date(2026, 6, 14)  # trap: June is partial
OUT = Path(__file__).parent / "data"

SKUS = {  # sku: unit price in cents
    "ETH-250": 1190, "COL-250": 990, "BRA-250": 850, "KEN-250": 1350,
    "DECAF-250": 1050, "ESP-1KG": 3290, "SAMPLER": 2400, "FILTERS": 450,
}
COUNTRIES = ["FR", "FR", "FR", "BE", "DE", "NL"]
B2B_CUSTOMER = "C0600"


def main():
    rng = random.Random(SEED)
    OUT.mkdir(exist_ok=True)

    customers = []
    for i in range(1, 601):
        segment = "business" if f"C{i:04d}" == B2B_CUSTOMER else "consumer"
        signup = START - timedelta(days=rng.randint(0, 400))
        customers.append([f"C{i:04d}", signup.isoformat(), rng.choice(COUNTRIES), segment])
    # Skewed popularity so some customers repeat often, most order once or twice.
    consumer_ids = [c[0] for c in customers if c[3] == "consumer"]
    weights = [1 / (k + 1) ** 0.6 for k in range(len(consumer_ids))]

    orders, items, refunds = [], [], []
    seq = 0
    d = START
    while d <= END:
        month_growth = 1 + 0.03 * (d.month - 1)
        lam = 7 * month_growth * (1.25 if d.weekday() >= 5 else 1.0)
        for _ in range(max(0, round(rng.gauss(lam, 1.5)))):
            seq += 1
            oid = f"O{seq:05d}"
            cust = rng.choices(consumer_ids, weights)[0]
            if rng.random() < 0.012:
                cust = ""  # trap: guest checkout, no customer id
            promo = rng.random() < 0.2
            n_lines = rng.randint(1, 3) + (1 if promo else 0)  # trap: promo orders are bigger by selection
            total = 0
            for line_no, sku in enumerate(rng.sample(list(SKUS), n_lines), 1):
                qty = rng.choice([1, 1, 1, 2, 2, 3])
                amount = qty * SKUS[sku]
                total += amount
                items.append([oid, line_no, sku, qty, cents(SKUS[sku]), cents(amount)])
            orders.append([oid, d.isoformat(), cust, cents(total), "SPRING10" if promo else ""])
            # Full refund a few days later, kept inside the same month so refund timing is unambiguous.
            if d.day <= 20 and rng.random() < 0.04:
                refunds.append((d + timedelta(days=rng.randint(1, 5)), cust, total))
        if d == date(2026, 3, 11):  # trap: one B2B bulk order, ~40x the median order
            seq += 1
            oid = f"O{seq:05d}"
            bulk_price = 2400  # negotiated, below list price
            items.append([oid, 1, "ESP-1KG", 80, cents(bulk_price), cents(80 * bulk_price)])
            orders.append([oid, d.isoformat(), B2B_CUSTOMER, cents(80 * bulk_price), ""])
        d += timedelta(days=1)

    for k, (rd, cust, total) in enumerate(refunds, 1):
        orders.append([f"R{k:04d}", rd.isoformat(), cust, cents(-total), ""])  # trap: refunds as negative rows
    orders.sort(key=lambda r: (r[1], r[0]))

    # trap: ~2% of sale rows exported twice (exact duplicates, adjacent)
    with_dupes = []
    for row in orders:
        with_dupes.append(row)
        if row[0].startswith("O") and rng.random() < 0.02:
            with_dupes.append(list(row))

    write("customers.csv", ["customer_id", "signup_date", "country", "segment"], customers)
    write("orders.csv", ["order_id", "order_date", "customer_id", "amount_eur", "promo_code"], with_dupes)
    write("order_items.csv", ["order_id", "line_no", "sku", "qty", "unit_price_eur", "line_amount_eur"], items)
    print(f"{len(customers)} customers, {len(with_dupes)} order rows "
          f"({len(with_dupes) - len(orders)} duplicates, {len(refunds)} refunds), {len(items)} item lines")


def cents(c):
    return f"{c / 100:.2f}"


def write(name, header, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    main()
