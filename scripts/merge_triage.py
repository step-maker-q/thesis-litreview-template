#!/usr/bin/env python3
"""
Merge per-batch triage decisions back onto the raw candidates list.

Reads:
  data/candidates_raw.csv
  data/triage_batches/batch_NN_triaged.csv  (one per batch)

Writes:
  data/candidates_triaged.csv    Stage 2 primary output
  data/triage_summary.md         Stage 2 summary report

Assigns paper_id sequentially to include and maybe rows in row order.

Reads target counts from protocol/topic.md if present.

Standalone. No AI required.
"""

import csv
import re
from collections import Counter
from pathlib import Path

RAW = Path("data/candidates_raw.csv")
BATCHES_DIR = Path("data/triage_batches")
OUT_CSV = Path("data/candidates_triaged.csv")
OUT_SUMMARY = Path("data/triage_summary.md")
TOPIC_FILE = Path("protocol/topic.md")


def load_targets():
    if not TOPIC_FILE.exists():
        return 50, 30
    text = TOPIC_FILE.read_text(encoding="utf-8")
    target_m = re.search(r"msc_target_includes:\s*(\d+)", text)
    min_m = re.search(r"msc_minimum_includes:\s*(\d+)", text)
    target = int(target_m.group(1)) if target_m else 50
    minimum = int(min_m.group(1)) if min_m else 30
    return target, minimum


def main():
    with open(RAW, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        raw_fields = reader.fieldnames
        raw_rows = list(reader)

    decisions = {}
    for batch_path in sorted(BATCHES_DIR.glob("batch_*_triaged.csv")):
        with open(batch_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                idx = row.get("row_index", "").strip()
                if not idx:
                    continue
                decisions[int(idx)] = {
                    "triage_label": row.get("triage_label", "").strip(),
                    "triage_reason": row.get("triage_reason", "").strip(),
                }

    if not decisions:
        print("no triage decisions found in", BATCHES_DIR)
        print("each batch_NN_triaged.csv must have row_index, triage_label, "
              "triage_reason columns")
        return

    target, minimum = load_targets()

    next_id = 1
    triaged_rows = []
    label_counts = Counter()
    exclusion_reason_counts = Counter()
    sample_includes = []

    for i, row in enumerate(raw_rows):
        d = decisions.get(i)
        if d is None:
            label = "exclude"
            reason = "missing triage decision (defaulted to exclude)"
        else:
            label = d["triage_label"]
            reason = d["triage_reason"]

        if label not in {"include", "exclude", "maybe"}:
            label = "exclude"
            reason = (reason + " || invalid label, defaulted to exclude").strip(" |")

        paper_id = ""
        if label in {"include", "maybe"}:
            paper_id = f"{next_id:03d}"
            next_id += 1

        out_row = {k: row.get(k, "") for k in raw_fields}
        out_row["triage_label"] = label
        out_row["triage_reason"] = reason
        out_row["paper_id"] = paper_id
        triaged_rows.append(out_row)
        label_counts[label] += 1

        if label == "exclude":
            short = reason.split(",")[0].split(".")[0].strip().lower()[:80]
            exclusion_reason_counts[short or "unspecified"] += 1
        if label == "include" and len(sample_includes) < 10:
            sample_includes.append(out_row)

    out_fields = list(raw_fields) + ["triage_label", "triage_reason"]
    if "paper_id" in out_fields:
        out_fields = [c for c in out_fields if c != "paper_id"]
    out_fields = ["paper_id"] + out_fields

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        for row in triaged_rows:
            writer.writerow({k: row.get(k, "") for k in out_fields})

    total = sum(label_counts.values())
    include_count = label_counts["include"]
    exclude_count = label_counts["exclude"]
    maybe_count = label_counts["maybe"]

    lines = []
    lines.append("# Triage summary\n\n")
    lines.append("Stage 2 output. Total raw count, label distribution, "
                 "top exclusion reasons, and a sample of included papers.\n\n")
    lines.append(f"## Total raw count\n\n{total} candidates evaluated.\n\n")
    lines.append("## Label distribution\n\n")
    lines.append(f"- include: {include_count}\n")
    lines.append(f"- maybe: {maybe_count}\n")
    lines.append(f"- exclude: {exclude_count}\n\n")
    lines.append("## Top exclusion reasons (first clause)\n\n")
    for reason, count in exclusion_reason_counts.most_common(5):
        lines.append(f"- {count}: {reason}\n")
    lines.append("\n")
    lines.append("## Warning\n\n")
    if include_count < minimum:
        lines.append(
            f"Include count is {include_count}, below the protocol minimum "
            f"of {minimum}. The {maybe_count} maybe rows may be re-triaged "
            f"at stage 4 after full text is available. If post-stage-4 "
            f"includes remain below the minimum, expand the stage 1 query "
            f"bank or add manual additions before continuing to synthesis.\n\n"
        )
    elif include_count > 2 * target:
        lines.append(
            f"Include count is {include_count}, above twice the target of "
            f"{target}. Consider tightening inclusion criteria.\n\n"
        )
    else:
        lines.append(f"Include count is within expected range "
                     f"(target {target}, minimum {minimum}).\n\n")

    lines.append("## Sample of included papers\n\n")
    for r in sample_includes:
        title = (r.get("title") or "").strip().replace("\n", " ")
        year = r.get("year", "")
        venue = r.get("venue", "") or "unknown venue"
        pid = r.get("paper_id", "")
        reason = (r.get("triage_reason") or "").strip()
        lines.append(f"- paper_{pid} ({year}, {venue}). {title}.\n  Reason: {reason}\n")

    OUT_SUMMARY.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {OUT_CSV} ({len(triaged_rows)} rows) and {OUT_SUMMARY}")
    print(f"include={include_count} maybe={maybe_count} exclude={exclude_count}")


if __name__ == "__main__":
    main()
