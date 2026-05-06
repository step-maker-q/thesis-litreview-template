#!/usr/bin/env python3
"""
Split successfully-downloaded paper IDs into batches for parallel deep-read
sub-agents. Round-robins paper IDs across batches so each batch has a
balanced mix.

Reads:
  data/candidates_triaged.csv
  data/download_log.csv

Writes:
  data/deepread_batches/batch_NN.txt   one paper_id per line

Standalone. No AI required.
"""

import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--triaged-csv", default="data/candidates_triaged.csv")
    parser.add_argument("--download-log", default="data/download_log.csv")
    parser.add_argument("--out-dir", default="data/deepread_batches")
    parser.add_argument("--num-batches", type=int, default=12)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("batch_*.txt"):
        old.unlink()

    downloaded_ids = []
    with open(args.download_log, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") in {"success", "already_present"}:
                downloaded_ids.append(row["paper_id"])

    with open(args.triaged_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        relevance = {}
        for row in reader:
            pid = row.get("paper_id", "")
            if pid:
                relevance[pid] = row.get("triage_label", "include")

    downloaded_ids.sort(key=lambda pid: (
        0 if relevance.get(pid) == "include" else 1,
        int(pid),
    ))

    batches = [[] for _ in range(args.num_batches)]
    for i, pid in enumerate(downloaded_ids):
        batches[i % args.num_batches].append(pid)

    for i, batch in enumerate(batches, 1):
        if not batch:
            continue
        path = out_dir / f"batch_{i:02d}.txt"
        path.write_text("\n".join(batch) + "\n", encoding="utf-8")
        print(f"wrote {len(batch)} ids to {path}")

    print(f"total ids distributed: {sum(len(b) for b in batches)}")


if __name__ == "__main__":
    main()
