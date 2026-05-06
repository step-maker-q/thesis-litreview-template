#!/usr/bin/env python3
"""
Append manual additions to data/candidates_raw.csv.

Manual additions are listed in protocol/search_queries.md under the
"Manual additions" section as YAML entries. The student curates this list
by hand. Typical entries: the historical anchor paper for the topic, the
closest direct prior work the student already knows, and papers behind
paywalls that the student has access to through their institution.

Each appended row is marked with source_database = manual_addition so
the PRISMA flow at stage seven can account for it separately.

Standalone. No AI required.

Usage:
    python scripts/append_manual_additions.py
"""

import csv
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required. Install with: pip install pyyaml")
    raise SystemExit(2)


CSV_PATH = Path("data/candidates_raw.csv")
QUERIES_PATH = Path("protocol/search_queries.md")


def extract_manual_additions(text: str) -> list[dict]:
    """Pull the YAML list block under '## Manual additions'."""
    section = re.search(
        r"## Manual additions\s*\n(.*?)(?=\n## |\Z)",
        text, re.DOTALL,
    )
    if not section:
        return []
    body = section.group(1)
    code_blocks = re.findall(r"```(?:yaml)?\n(.*?)```", body, re.DOTALL)
    additions = []
    for block in code_blocks:
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, list):
            additions.extend([p for p in parsed if isinstance(p, dict)])
    return additions


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run stage 1 first.")
        raise SystemExit(2)
    if not QUERIES_PATH.exists():
        print(f"ERROR: {QUERIES_PATH} not found.")
        raise SystemExit(2)

    text = QUERIES_PATH.read_text(encoding="utf-8")
    additions = extract_manual_additions(text)
    if not additions:
        print("no manual additions found in protocol/search_queries.md")
        return

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    existing_titles = {r["title"].strip().lower() for r in existing}
    appended = 0

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for add in additions:
            title = (add.get("title") or "").strip()
            if not title or title.lower() in existing_titles:
                continue
            row = {k: "" for k in fieldnames}
            row.update({
                "title": title,
                "authors": add.get("authors", ""),
                "year": str(add.get("year", "")),
                "venue": add.get("venue", ""),
                "abstract": add.get("abstract", ""),
                "doi": add.get("doi", ""),
                "arxiv_id": add.get("arxiv_id", ""),
                "url": add.get("url", ""),
                "pdf_url": add.get("pdf_url", ""),
                "source_database": "manual_addition",
                "source_query": "manual_addition: " + (add.get("reason", "") or ""),
            })
            writer.writerow(row)
            appended += 1

    print(f"appended {appended} manual additions, total rows now "
          f"{len(existing) + appended}")


if __name__ == "__main__":
    main()
