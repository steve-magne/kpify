"""List numbers in 06-executive-summary.md that appear nowhere in kpi-results.json, 02-data-profile.md
or 04-analysis.md. Stdlib only. Exit 1 if any.

    python3 trace_numbers.py <analysis-dir>

A quote matches a source within its own rounding (47 matches 46.8), and a ratio may be quoted as a
percentage (0.47 → 47%). Dates and integers up to 31 are ignored.
"""

import json
import re
import sys
from pathlib import Path

# Thousands use "," or a non-breaking space; a decimal uses "." or a "," not followed by exactly 3 digits.
NUMBER = re.compile(r"(?<![\w.])-?(\d{1,3}(?:[,  ]\d{3})+|\d+)([.,]\d+)?\s?([kK]\b)?")
DATE = re.compile(r"\b\d{4}-\d{2}(-\d{2})?\b")


def numbers(text):
    """Yield (value, half of the last shown digit) so rounded quotes still match."""
    for m in NUMBER.finditer(DATE.sub(" ", text)):
        whole = re.sub(r"[,  ]", "", m.group(1))
        frac = (m.group(2) or "").replace(",", ".")
        scale = 1000 if m.group(3) else 1
        yield float(whole + frac) * scale, 0.5 * 10 ** -max(len(frac) - 1, 0) * scale


def close(a, b):
    return abs(a - b) <= max(0.005 * abs(b), 0.0005)


def prose_numbers(texts, results_path):
    """Numbers in texts["06-executive-summary.md"] that no source contains."""
    sources = {v for v, _ in numbers(texts.get("02-data-profile.md", "") + texts.get("04-analysis.md", ""))}
    if Path(results_path).exists():
        try:
            for r in json.loads(Path(results_path).read_text()):
                try:
                    sources.add(float(r["value"]))
                except (TypeError, ValueError, KeyError):
                    pass
        except (json.JSONDecodeError, TypeError):
            pass
    sources |= {v * 100 for v in sources}  # ratios quoted as percentages
    # ponytail: integers up to 31 are skipped (day counts, list numbers); upgrade if they hide real misquotes.
    return sorted({v for v, half in numbers(texts["06-executive-summary.md"])
                   if not (v == int(v) and abs(v) <= 31)
                   and not any(close(v, s) or abs(v - s) <= half + 1e-9 for s in sources)})


def main():
    analysis = Path(sys.argv[1] if len(sys.argv) > 1 else "analysis")
    names = ["02-data-profile.md", "04-analysis.md", "06-executive-summary.md"]
    texts = {n: (analysis / n).read_text() for n in names if (analysis / n).exists()}
    untraced = prose_numbers(texts, analysis / "kpi-results.json")
    for line in texts["06-executive-summary.md"].splitlines():
        hits = [v for v, _ in numbers(line) if v in untraced]
        if hits:
            print(f"UNTRACED {hits}: {line.strip()}")
    print(f"{len(untraced)} untraced number(s)")
    sys.exit(1 if untraced else 0)


if __name__ == "__main__":
    main()
