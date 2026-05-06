#!/usr/bin/env python3
"""
Split data/candidates_raw.csv into N batches for parallel triage.

Writes data/triage_batches/batch_NN.csv with the same columns as the input
plus a row_index column. After triage, merge_triage.py reassembles the
batches into data/candidates_triaged.csv.

Standalone. No AI required.

Usage:
    python scripts/split_for_triage.py
    python scripts/split_for_triage.py --num-batches 8
"""

import argparse
import csv
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/candidates_raw.csv")
    parser.add_argument("--out-dir", default="data/triage_batches")
    parser.add_argument("--num-batches", type=int, default=8)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("batch_*.csv"):
        old.unlink()

    with open(args.input, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    for i, row in enumerate(rows):
        row["row_index"] = str(i)

    out_fields = ["row_index"] + list(fieldnames)
    n = len(rows)
    batch_size = math.ceil(n / args.num_batches)

    for b in range(args.num_batches):
        start = b * batch_size
        end = min(start + batch_size, n)
        if start >= end:
            break
        batch = rows[start:end]
        path = out_dir / f"batch_{b+1:02d}.csv"
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            for r in batch:
                writer.writerow(r)
        print(f"wrote {len(batch)} rows to {path}")

    print(f"total rows split: {n} into up to {args.num_batches} batches")


if __name__ == "__main__":
    main()
