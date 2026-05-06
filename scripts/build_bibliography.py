#!/usr/bin/env python3
"""
Build a flat list of every source reviewed in this run.

Outputs:
  synthesis/sources.md   One entry per paper. First-author alphabetical.
                         Each entry has author, year, title, venue, link, and
                         a one-line "what it does" summary.
  synthesis/sources.bib  BibTeX equivalent.

Reads notes/paper_*.md. No tiering, no filtering, no relevance gates.

Standalone. No AI required.
"""

import re
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required. Install with: pip install pyyaml")
    raise SystemExit(2)


NOTES_DIR = Path("notes")
TOPIC_FILE = Path("protocol/topic.md")
OUT_MD = Path("synthesis/sources.md")
OUT_BIB = Path("synthesis/sources.bib")


def parse_note(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return fm, m.group(2)


def first_sentence(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return sentences[0].strip() if sentences else ""


def normalize_authors(authors):
    if not authors:
        return ["Unknown"]
    if isinstance(authors, str):
        return [a.strip() for a in re.split(r",\s*|\s+and\s+", authors) if a.strip()]
    return [str(a).strip() for a in authors if str(a).strip()]


def first_author_lastname(authors):
    a = normalize_authors(authors)[0]
    parts = a.split()
    return parts[-1] if parts else "Unknown"


def asciify(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )


def cite_key(record):
    last = asciify(first_author_lastname(record.get("authors") or []))
    last = re.sub(r"[^A-Za-z]", "", last) or "Unknown"
    year = str(record.get("year") or "n.d.").strip()
    title = (record.get("title") or "").strip().lower()
    title_word = ""
    for word in re.split(r"\W+", title):
        if word and word not in {"a", "an", "the", "of", "for", "and",
                                  "to", "on", "in", "with", "is"}:
            title_word = word
            break
    return f"{last}{year}{title_word.capitalize()}"


def authors_md(authors):
    a = normalize_authors(authors)
    if len(a) == 1:
        return a[0]
    if len(a) == 2:
        return f"{a[0]} and {a[1]}"
    return f"{a[0]} et al."


def venue_md(venue):
    venue = (venue or "").strip()
    if not venue or venue.lower() in {"unknown", "unknown venue"}:
        return ""
    return venue


def url_for(record):
    if record.get("doi"):
        return f"https://doi.org/{record['doi']}"
    if record.get("arxiv_id"):
        aid = record["arxiv_id"].strip()
        if aid:
            return f"https://arxiv.org/abs/{aid}"
    return record.get("url", "") or ""


def short_summary(fm: dict, body: str) -> str:
    primary = ((fm.get("claims") or {}).get("primary_contribution") or "").strip()
    if primary:
        return primary.rstrip(".") + "."
    rel_section = re.search(
        r"##\s+Relevance to the thesis topic\s*\n(.*?)(?:\n##\s|\Z)",
        body, re.DOTALL,
    )
    if rel_section:
        s = first_sentence(rel_section.group(1))
        if s:
            return s.rstrip(".") + "."
    method = re.search(
        r"##\s+Method summary\s*\n(.*?)(?:\n##\s|\Z)", body, re.DOTALL,
    )
    if method:
        s = first_sentence(method.group(1))
        if s:
            return s.rstrip(".") + "."
    return ""


def bibtex_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def bibtex_authors(authors):
    return " and ".join(normalize_authors(authors))


def write_bibtex_entry(record):
    venue = (record.get("venue") or "").strip()
    venue_lower = venue.lower()
    has_journal = any(
        w in venue_lower
        for w in ["journal", "transactions", "letters",
                  "communications", "magazine", "review", "advances"]
    )
    has_book = any(
        w in venue_lower
        for w in ["proceedings", "conference",
                  "symposium", "workshop"]
    )
    if has_journal:
        kind = "article"
    elif has_book:
        kind = "inproceedings"
    else:
        kind = "misc"

    lines = [f"@{kind}{{{cite_key(record)},"]
    lines.append(f'  author = {{{bibtex_escape(bibtex_authors(record.get("authors") or []))}}},')
    title = bibtex_escape((record.get("title") or "").strip())
    lines.append(f'  title  = {{{title}}},')
    if record.get("year"):
        lines.append(f'  year   = {{{record["year"]}}},')
    if venue:
        if kind == "article":
            lines.append(f'  journal = {{{bibtex_escape(venue)}}},')
        elif kind == "inproceedings":
            lines.append(f'  booktitle = {{{bibtex_escape(venue)}}},')
        else:
            lines.append(f'  howpublished = {{{bibtex_escape(venue)}}},')
    if record.get("doi"):
        lines.append(f'  doi    = {{{record["doi"]}}},')
    if record.get("arxiv_id"):
        lines.append(f'  eprint = {{{record["arxiv_id"]}}},')
        lines.append('  archivePrefix = {arXiv},')
    if not record.get("doi") and record.get("url"):
        lines.append(f'  url    = {{{record["url"]}}},')
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("}")
    return "\n".join(lines) + "\n"


def load_topic_title():
    if not TOPIC_FILE.exists():
        return ""
    text = TOPIC_FILE.read_text(encoding="utf-8")
    m = re.search(r"title:\s*(.+)", text)
    return m.group(1).strip() if m else ""


def main():
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted(NOTES_DIR.glob("paper_*.md")):
        parsed = parse_note(path)
        if not parsed:
            continue
        fm, body = parsed
        records.append({
            "paper_id": fm.get("paper_id", ""),
            "title": (fm.get("title") or "").strip(),
            "authors": fm.get("authors") or [],
            "year": fm.get("year", 0) or 0,
            "venue": fm.get("venue", "") or "",
            "doi": (fm.get("doi") or "").strip(),
            "arxiv_id": (fm.get("arxiv_id") or "").strip(),
            "url": (fm.get("url") or "").strip(),
            "summary": short_summary(fm, body),
        })

    records.sort(key=lambda r: (
        asciify(first_author_lastname(r["authors"])).lower(),
        -int(r["year"] or 0),
        r["title"].lower(),
    ))

    topic_title = load_topic_title()
    md = []
    md.append("# Sources\n\n")
    md.append(f"All {len(records)} sources reviewed at full text in this "
              "literature review run, sorted by first-author surname. "
              "Each entry shows what the paper does in one line. Cite keys "
              "follow the `LastnameYearTitleword` convention and the BibTeX "
              "equivalent is at `synthesis/sources.bib`.\n\n")
    if topic_title:
        md.append(f"Active topic. {topic_title}.\n\n")

    md.append("## Sources\n\n")
    for r in records:
        authors = authors_md(r["authors"])
        year = r["year"] or "n.d."
        title = r["title"]
        venue = venue_md(r["venue"])
        url = url_for(r)
        ck = cite_key(r)
        line = f"- **{authors} ({year}).** *{title}*."
        if venue:
            line += f" {venue}."
        if url:
            line += f" [link]({url})"
        line += f" `[{ck}, paper_{r['paper_id']}]`"
        md.append(line + "\n")
        if r["summary"]:
            md.append(f"  - {r['summary']}\n")

    OUT_MD.write_text("".join(md), encoding="utf-8")

    bib_lines = []
    bib_lines.append("% Sources reviewed at full text. Auto-generated from notes/.\n")
    bib_lines.append("% Sorted by first-author surname.\n\n")
    for r in records:
        bib_lines.append(write_bibtex_entry(r))
        bib_lines.append("\n")
    OUT_BIB.write_text("".join(bib_lines), encoding="utf-8")

    print(f"wrote {OUT_MD} ({len(records)} sources)")
    print(f"wrote {OUT_BIB}")


if __name__ == "__main__":
    main()
