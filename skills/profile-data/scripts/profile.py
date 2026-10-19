"""Deterministic first-pass profile of CSV/TSV/JSON/JSONL files. Stdlib only; prints Markdown.

    python3 profile.py FILE [FILE ...]

Per table: rows, exact duplicate rows, and per column: inferred type, blanks, distinct values,
candidate key, range, negatives, skew/outliers, last-period coverage for dates.
JSON is flattened: nested objects become dotted columns (`customer.id`), lists of objects become
child tables (`orders.json.items`), lists of scalars one comma-joined cell, with `_parent_id` pointing at the parent's `id` (or row number).
Across tables: shared column names, and differently named id columns whose values fall inside
another table's unique column, with orphan counts and join cardinality, plus a Mermaid diagram.
It only reports; it never cleans or drops anything.
"""

import calendar
import csv
import json
import re
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


def read_json(path):
    """JSON array, {"key": [...]} wrapper or JSON Lines → {table name: (header, rows)}."""
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in (".jsonl", ".ndjson"):
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        data = json.loads(text)
    if isinstance(data, dict):
        lists = [v for v in data.values() if isinstance(v, list)]
        data = lists[0] if len(lists) == 1 else [data]  # ponytail: one top-level list, else the object is the row
    tables = {}
    flatten(tables, path.name, data)
    return tables


def flatten(tables, name, records):
    tables[name] = None  # reserve the slot so a parent prints before its children
    rows, children = [], {}
    for n, rec in enumerate(records, 1):
        row = {}
        rec = rec if isinstance(rec, dict) else {"value": rec}
        walk(rec, "", row, children, name, rec.get("id", n))
        rows.append(row)
    header = list(dict.fromkeys(k for r in rows for k in r))
    tables[name] = (header, [[r.get(k, "") for k in header] for r in rows])
    for child, recs in children.items():
        flatten(tables, child, recs)


def walk(obj, prefix, row, children, name, parent_id):
    for k, v in obj.items():
        key = prefix + k
        if isinstance(v, dict):
            walk(v, key + ".", row, children, name, parent_id)
        elif isinstance(v, list) and any(isinstance(x, dict) for x in v):
            children.setdefault(f"{name}.{key}", []).extend(
                {"_parent_id": parent_id, **x} if isinstance(x, dict) else {"_parent_id": parent_id, "value": x} for x in v)
        else:
            row[key] = cell(v)


def cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, list):
        return ", ".join(map(cell, v))
    return str(v)


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
        suffix = path.suffix.lower()
        if suffix in (".csv", ".tsv"):
            tables[path.name] = read(path)
        elif suffix in (".json", ".jsonl", ".ndjson"):
            tables.update(read_json(path))
        else:
            print(f"## {path.name}\n\nSkipped: only CSV/TSV/JSON. Convert first, e.g. with DuckDB:\n"
                  f"`uv run --with duckdb python -c \"import duckdb; duckdb.sql(\\\"COPY (SELECT * FROM '{path}') TO '{path.stem}.csv'\\\")\"`\n")

    for name, (header, rows) in tables.items():
        dupes = len(rows) - len(set(map(tuple, rows)))
        ragged = sum(len(r) != len(header) for r in rows)
        print(f"## {name}\n")
        print(f"- Rows: {len(rows)}; columns: {len(header)}")
        print(f"- Exact duplicate rows: {dupes} extra copies" + (f" ({pct(dupes, len(rows))})" if dupes else ""))
        if ragged:
            print(f"- Rows with a different column count than the header: {ragged}")
        print("\n| Column | Type | Blank/null | Distinct | Range | Notes |\n|---|---|---|---|---|---|")
        for i, col in enumerate(header):
            print(profile_column(col, [r[i] if i < len(r) else "" for r in rows], len(rows)))
        print()
        by_month(header, rows)

    names = list(tables)
    shared = []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            for col in sorted(set(tables[names[a]][0]) & set(tables[names[b]][0])):
                shared.append((names[a], col, names[b], col))
    edges = []
    if shared:
        print("## Shared columns (possible joins)\n\n| Left | Right | Column | Left values not in right | Right values not in left | Cardinality |\n|---|---|---|---|---|---|")
        for left, col, right, _ in shared:
            orphans_l, orphans_r, card, overlap = join_stats(tables, left, col, right, col)
            print(f"| {left} | {right} | {col} | {orphans_l} | {orphans_r} | {card} |")
            if overlap:
                edges.append((left, col, right, col, card))
    inferred = inferred_joins(tables)
    if inferred:
        print("\n## Inferred joins (different names, value overlap)\n\nCandidates only: confirm by meaning before using one.\n\n"
              "| From | Column | To | Column | From values not in to | Coverage | Cardinality |\n|---|---|---|---|---|---|---|")
        for left, lcol, right, rcol in inferred:
            orphans_l, _, card, overlap = join_stats(tables, left, lcol, right, rcol)
            print(f"| {left} | {lcol} | {right} | {rcol} | {orphans_l} | {pct(overlap, overlap + orphans_l)} | {card} |")
            edges.append((left, lcol, right, rcol, card))
    if edges:
        ids = {n: f"t{i}" for i, n in enumerate(names)}
        print("\n## Relationship diagram\n\n```mermaid\nflowchart LR")
        for n in sorted({e[0] for e in edges} | {e[2] for e in edges}, key=names.index):
            print(f'  {ids[n]}["{n}"]')
        for left, lcol, right, rcol, card in edges:
            label = lcol if lcol == rcol else f"{lcol} → {rcol}"
            print(f'  {ids[left]} -- "{label} ({card})" --> {ids[right]}')
        print("```")


ID_NAME = re.compile(r"((^|[_.\s-])(id|key|code|ref|uuid)|[a-z0-9](Id|Key|Code|Ref|Uuid|ID))$", re.I)


def inferred_joins(tables):
    """Id-like columns whose distinct values sit ≥50% inside a differently named unique column.
    ponytail: all-pairs set scan, O(columns²); fine for profiling, sample if it gets slow."""
    cols = {(t, c): column(tables[t], c) for t in tables for c in tables[t][0]}
    keys = {k: set(v) for k, v in cols.items() if v and len(v) == len(set(v))}
    found = []
    for (t, c), values in cols.items():
        fk = set(values)
        if len(fk) < 3 or not ID_NAME.search(c):
            continue
        for (kt, kc), pk in keys.items():
            if kc != c and (kt, kc) != (t, c) and len(fk & pk) >= 0.5 * len(fk):
                found.append((t, c, kt, kc))
    return found


def join_stats(tables, left, lcol, right, rcol):
    lv, rv = column(tables[left], lcol), column(tables[right], rcol)
    ls, rs = set(lv), set(rv)
    card = f"{'1' if len(lv) == len(ls) else 'N'}:{'1' if len(rv) == len(rs) else 'N'}"
    return len(ls - rs), len(rs - ls), card, len(ls & rs)


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
