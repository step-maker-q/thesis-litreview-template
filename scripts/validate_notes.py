#!/usr/bin/env python3
"""
Note schema validator. Stage 4 helper.

Validates every note file in notes/ against the schema defined in
protocol/note_schema.md. Notes that fail validation are listed with the
specific error.

Allowed values for `category` and `method.family` are read from
protocol/topic.md. The literal string "other" is always allowed.

Standalone. No AI required.

Usage:
    python scripts/validate_notes.py
    python scripts/validate_notes.py --strict   (exit non-zero on any failure)
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required. Install with: pip install pyyaml")
    sys.exit(2)


REQUIRED_FRONTMATTER_KEYS = [
    "paper_id", "title", "authors", "year", "venue",
    "pdf_path", "read_date",
    "category", "method", "ground_truth", "evaluation",
    "claims", "limitations_authors_state",
    "quality_flags", "relevance",
]

NOVELTY_VALUES = {"strong", "moderate", "incremental", "unclear"}
RELEVANCE_VALUES = {"core", "adjacent", "peripheral"}

REQUIRED_BODY_SECTIONS = [
    "Problem statement",
    "Method summary",
    "Ground truth and evaluation",
    "Stated limitations",
    "Gaps this paper opens",
    "Relevance to the thesis topic",
]


def load_topic_enums(topic_path: str):
    if not Path(topic_path).exists():
        return None, None
    text = Path(topic_path).read_text(encoding="utf-8")

    cat_block = re.search(r"categories:\s*\n((?:\s*-\s*\S+\n?)+)", text)
    method_block = re.search(r"method_families:\s*\n((?:\s*-\s*\S+\n?)+)", text)

    def parse_block(block_text):
        items = re.findall(r"-\s*(\S+)", block_text)
        return {i for i in items if not i.startswith("replace_with")}

    categories = parse_block(cat_block.group(1)) if cat_block else set()
    methods = parse_block(method_block.group(1)) if method_block else set()
    categories.add("other")
    methods.add("other")
    return categories, methods


def parse_note(path: Path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        return None, None, "missing or malformed frontmatter delimiters"
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return None, None, f"YAML parse error: {e}"
    body = match.group(2)
    return frontmatter, body, None


def check_frontmatter(fm: dict, paper_id_from_filename: str,
                       allowed_categories, allowed_method_families):
    errors = []
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in fm:
            errors.append(f"missing key: {key}")
        elif fm[key] in (None, "", []):
            errors.append(f"empty value for required key: {key}")

    if "paper_id" in fm and str(fm["paper_id"]) != paper_id_from_filename:
        errors.append(
            f"paper_id mismatch: frontmatter has {fm['paper_id']!r}, "
            f"filename has {paper_id_from_filename!r}"
        )

    if isinstance(fm.get("year"), int) and not (1990 <= fm["year"] <= 2030):
        errors.append(f"implausible year: {fm['year']}")

    if allowed_categories and isinstance(fm.get("category"), list):
        for v in fm["category"]:
            if v not in allowed_categories:
                errors.append(f"category has invalid value: {v}")

    if isinstance(fm.get("method"), dict):
        family = fm["method"].get("family")
        if allowed_method_families and family and family not in allowed_method_families:
            errors.append(f"method.family has invalid value: {family}")

    if isinstance(fm.get("ground_truth"), dict):
        if not isinstance(fm["ground_truth"].get("external"), bool):
            errors.append("ground_truth.external must be boolean")
        if not isinstance(fm["ground_truth"].get("reproducible"), bool):
            errors.append("ground_truth.reproducible must be boolean")

    if isinstance(fm.get("claims"), dict):
        novelty = fm["claims"].get("novelty_strength")
        if novelty and novelty not in NOVELTY_VALUES:
            errors.append(f"claims.novelty_strength has invalid value: {novelty}")

    if isinstance(fm.get("relevance"), dict):
        rel = fm["relevance"].get("relevance_to_topic")
        if rel and rel not in RELEVANCE_VALUES:
            errors.append(f"relevance.relevance_to_topic has invalid value: {rel}")

    if isinstance(fm.get("quality_flags"), dict):
        for flag in [
            "self_constructed_ground_truth", "comparison_table_only",
            "hobby_project_scale", "predictable_outcome",
        ]:
            if flag in fm["quality_flags"] and not isinstance(
                fm["quality_flags"][flag], bool
            ):
                errors.append(f"quality_flags.{flag} must be boolean")

    return errors


def check_body(body: str):
    errors = []
    found_sections = re.findall(r"^##\s+(.+?)$", body, re.MULTILINE)
    for required in REQUIRED_BODY_SECTIONS:
        if required not in found_sections:
            errors.append(f"missing body section: {required}")

    word_count = len(body.split())
    if word_count < 400:
        errors.append(f"body too short: {word_count} words, minimum 400")
    if word_count > 1500:
        errors.append(f"body too long: {word_count} words, maximum 1500")

    gaps_match = re.search(
        r"##\s+Gaps this paper opens\s*\n(.*?)(?=\n##\s|\Z)",
        body, re.DOTALL
    )
    if gaps_match:
        gap_text = gaps_match.group(1).strip()
        if len(gap_text.split()) < 30:
            errors.append("gaps_opened section is too short, "
                          "needs 3-6 specific gap statements")

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notes-dir", default="notes")
    parser.add_argument("--topic-file", default="protocol/topic.md")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero on any validation failure")
    args = parser.parse_args()

    notes_dir = Path(args.notes_dir)
    if not notes_dir.exists():
        print(f"notes directory not found: {notes_dir}")
        sys.exit(2)

    note_files = sorted(notes_dir.glob("paper_*.md"))
    if not note_files:
        print(f"no notes found in {notes_dir}")
        sys.exit(2)

    allowed_categories, allowed_method_families = load_topic_enums(args.topic_file)
    if allowed_categories is None:
        print(f"warning: could not load topic enums from {args.topic_file}, "
              "skipping category and method.family validation")

    total = len(note_files)
    passed = 0
    failed_files = []

    for path in note_files:
        m = re.match(r"paper_(\d+)\.md$", path.name)
        if not m:
            failed_files.append((path.name, ["filename does not match paper_NNN.md"]))
            continue
        paper_id = m.group(1)

        frontmatter, body, parse_error = parse_note(path)
        if parse_error:
            failed_files.append((path.name, [parse_error]))
            continue

        errors = []
        errors.extend(check_frontmatter(
            frontmatter or {}, paper_id,
            allowed_categories, allowed_method_families,
        ))
        errors.extend(check_body(body or ""))

        if errors:
            failed_files.append((path.name, errors))
        else:
            passed += 1

    print(f"validated {total} notes. {passed} passed, {len(failed_files)} failed.")
    if failed_files:
        print()
        for filename, errors in failed_files:
            print(f"  {filename}")
            for err in errors:
                print(f"    - {err}")

    if args.strict and failed_files:
        sys.exit(1)


if __name__ == "__main__":
    main()
