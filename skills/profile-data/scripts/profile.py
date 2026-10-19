"""Deterministic first-pass profile of CSV/TSV files. Stdlib only; prints Markdown.

    python3 profile.py FILE [FILE ...]

Per file: rows, exact duplicate rows, and per column: inferred type, blanks, distinct values,
candidate key, range, negatives, skew/outliers, last-period coverage for dates.
Across files: shared column names with orphan counts and join cardinality.
It only reports; it never cleans or drops anything.
"""

import calendar
import csv
import statistics
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

NULL_LIKE = {"na", "n/a", "null", "none", "nan", "-", "?"}


def parse_number(s):
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date() if len(s) >= 10 else None
    except ValueError:
        return None


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f, delimiter="\t" if path.suffix.lower() == ".tsv" else ","))
    return rows[0], rows[1:]


def profile_column(name, values, n_rows):
    present = [v.strip() for v in values if v.strip() and v.strip().lower() not in NULL_LIKE]
    blanks = sum(1 for v in values if not v.strip())
    null_like = n_rows - blanks - len(present)
    distinct = len(set(present))
    numbers = [x for x in map(parse_number, present) if x is not None]
    dates = [x for x in map(parse_date, present) if x is not None]

    notes = []
    if present and len(dates) == len(present):
        kind = "date"
        lo, hi = min(dates), max(dates)
        days = calendar.monthrange(hi.year, hi.month)[1]
        rng = f"{lo} → {hi}"
        if hi.day < days:
            notes.append(f"last month {hi:%Y-%m} covers {hi.day}/{days} days")
    elif present and len(numbers) == len(present):
        kind = "integer" if all(x == int(x) for x in numbers) else "decimal"
        lo, hi = min(numbers), max(numbers)
        rng = f"{fmt(lo)} → {fmt(hi)}"
        neg = sum(x < 0 for x in numbers)
        if neg:
            notes.append(f"{neg} negative")
        positive = [x for x in numbers if x > 0]
        if len(positive) >= 20:
            med = statistics.median(positive)
            outliers = sorted(x for x in positive if x > 10 * med)
            notes.append(f"median {fmt(med)}")
            if outliers:
                notes.append(f"{len(outliers)} value(s) >10× median, max {fmt(outliers[-1])} ({outliers[-1] / med:.0f}×)")
    else:
        kind = "text"
        rng = ""
        if len(numbers) > 0.9 * len(present):
            notes.append(f"mostly numeric: {len(present) - len(numbers)} non-numeric")
        if distinct <= 12:
            top = Counter(present).most_common(6)
            notes.append("values: " + ", ".join(f"{v} ({c})" for v, c in top))
        variants = len({v.lower() for v in present})
        if variants < distinct:
            notes.append(f"{distinct - variants} case variants")
    if present and distinct == n_rows:
        notes.insert(0, "unique (candidate key)")
    elif name.lower().endswith("id") and distinct < len(present) and distinct > n_rows * 0.5:
        notes.insert(0, f"{len(present) - distinct} repeated ids")
    if null_like:
        notes.append(f"{null_like} null-like tokens")
    return f"| {name} | {kind} | {pct(blanks + null_like, n_rows)} | {distinct} | {rng} | {'; '.join(notes)} |"


def main(paths):
    tables = {}
    for path in map(Path, paths):
        if path.suffix.lower() not in (".csv", ".tsv"):
            print(f"## {path.name}\n\nSkipped: only CSV/TSV. Convert first, e.g. with DuckDB:\n"
                  f"`uv run --with duckdb python -c \"import duckdb; duckdb.sql(\\\"COPY (SELECT * FROM '{path}') TO '{path.stem}.csv'\\\")\"`\n")
            continue
        header, rows = read(path)
        tables[path.name] = (header, rows)
        dupes = len(rows) - len(set(map(tuple, rows)))
        ragged = sum(len(r) != len(header) for r in rows)
        print(f"## {path.name}\n")
        print(f"- Rows: {len(rows)}; columns: {len(header)}")
        print(f"- Exact duplicate rows: {dupes} extra copies" + (f" ({pct(dupes, len(rows))})" if dupes else ""))
        if ragged:
            print(f"- Rows with a different column count than the header: {ragged}")
        print("\n| Column | Type | Blank/null | Distinct | Range | Notes |\n|---|---|---|---|---|---|")
        for i, name in enumerate(header):
            print(profile_column(name, [r[i] if i < len(r) else "" for r in rows], len(rows)))
        print()
        by_month(header, rows)

    names = list(tables)
    shared = []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            for col in sorted(set(tables[names[a]][0]) & set(tables[names[b]][0])):
                shared.append((names[a], names[b], col))
    if shared:
        print("## Shared columns (possible joins)\n\n| Left | Right | Column | Left values not in right | Right values not in left | Cardinality |\n|---|---|---|---|---|---|")
        for left, right, col in shared:
            lv, rv = column(tables[left], col), column(tables[right], col)
            ls, rs = set(lv), set(rv)
            card = f"{'1' if len(lv) == len(ls) else 'N'}:{'1' if len(rv) == len(rs) else 'N'}"
            print(f"| {left} | {right} | {col} | {len(ls - rs)} | {len(rs - ls)} | {card} |")


def by_month(header, rows):
    """Issue counts per month of the first date column, so breakdowns are counted, not estimated."""
    cols = list(zip(*rows)) if rows else []
    date_i = next((i for i, c in enumerate(cols)
                   if all(parse_date(v.strip()) for v in c if v.strip())), None)
    if date_i is None:
        return
    neg = [i for i, c in enumerate(cols) if any((x := parse_number(v)) is not None and x < 0 for v in c)]
    blank = [i for i, c in enumerate(cols) if any(not v.strip() for v in c)]
    stats, seen = {}, set()
    for r in rows:
        m = stats.setdefault(r[date_i].strip()[:7], Counter())
        m["rows"] += 1
        m["dup"] += tuple(r) in seen
        seen.add(tuple(r))
        for i in neg:
            m[f"neg{i}"] += (parse_number(r[i]) or 0) < 0
        for i in blank:
            m[f"blank{i}"] += not r[i].strip()
    heads = ["Rows", "Extra duplicate copies"] + [f"{header[i]} < 0" for i in neg] + [f"{header[i]} blank" for i in blank]
    keys = ["rows", "dup"] + [f"neg{i}" for i in neg] + [f"blank{i}" for i in blank]
    print(f"By month of `{header[date_i]}`:\n\n| Month | " + " | ".join(heads) + " |\n|" + "---|" * (len(heads) + 1))
    for month in sorted(stats):
        print(f"| {month} | " + " | ".join(str(stats[month][k]) for k in keys) + " |")
    print()


def column(table, col):
    header, rows = table
    i = header.index(col)
    return [r[i].strip() for r in rows if i < len(r) and r[i].strip()]


def fmt(x):
    return f"{x:,.2f}".rstrip("0").rstrip(".") if x != int(x) else f"{int(x):,}"


def pct(n, total):
    return f"{100 * n / total:.1f}%" if total else "0%"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
