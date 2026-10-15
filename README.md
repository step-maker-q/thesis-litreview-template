# Thesis Literature Review Pipeline (Template)

A reproducible scaffold for running the literature review of an MSc or BSc thesis on any topic. The pipeline produces a documented search protocol, structured per-paper notes, a gap matrix, an indicator-based quality assessment, and a one-page positioning statement.

The pipeline runs in three modes.

- **100% no-AI mode.** Two Python scripts, a spreadsheet, a markdown editor, and a PDF reader. No LLM, no API key, no agentic tool. See "No-AI walkthrough" below.
- **Single-shot LLM mode.** Each stage prompt is a self-contained markdown file. Paste the prompt and the input artifact into any chat LLM and write the response back to the named output path.
- **Agentic AI mode.** Any agentic coding tool that can delegate work to parallel sub-tasks (Claude Code, OpenCode, Aider, Cursor, Codex, Continue, custom orchestrators built on the Anthropic or OpenAI APIs). The agent definitions in `agents/` are written in vendor-neutral language.

Pick the mode that fits your tooling. You can mix modes per stage. The handoff between every stage is a named file on disk, so it does not matter who or what produced it.

## No-AI walkthrough

The full pipeline runs without any AI.

What you need: Python 3.10+, a spreadsheet program (Excel, Numbers, LibreOffice Calc, Google Sheets), a markdown editor (VS Code, Sublime, Obsidian, plain text editor), and a PDF reader.

What the scripts do for you (no AI, no judgment): stage 1 search, stage 3 download, stage 4 schema validation, optional bibliography generation.

What you do by hand: stage 2 triage, stage 4 deep read, stage 5 synthesis, stage 6 quality filter, stage 7 positioning. Each agent file in `agents/` has a "Run by hand" section with the exact procedure.

```
Stage 1  make search                Script. Runs queries, dedupes, writes data/candidates_raw.csv.
Stage 2  By hand                    Open the CSV in a spreadsheet. Fill triage_label, triage_reason,
                                    paper_id columns. Save as data/candidates_triaged.csv.
                                    Write data/triage_summary.md from the totals.
Stage 3  make download              Script. Fetches PDFs, builds manual-retrieval list for paywalled.
Stage 4  By hand + make validate    Read each PDF. Copy the template from the bottom of
                                    agents/04_deepread.md into notes/paper_NNN.md. Fill it in.
                                    Run make validate to catch schema errors.
Stage 5  By hand                    Build a markdown table (categories x method families) from
                                    the note frontmatter. Write 5-10 gap candidates.
Stage 6  By hand                    Score each candidate against the seven indicators in
                                    protocol/indicator_rubric.md. Write the verdict table.
Stage 7  By hand                    Read the top 5 competitor notes. Write positioning_statement.md
                                    and prisma_flow.md. Numbers come from the search log and CSV counts.
```

The deep read at stage 4 is the load-bearing work. No tool reads the papers for you in by-hand mode, and everything downstream depends on the notes being substantive. Pace yourself, take breaks between papers, and read in tiers (start with papers you marked as core relevance during triage).

## Who this is for

Students starting an MSc or BSc thesis who need to produce a defensible literature review and a positioning statement before writing the proposal. The scaffold enforces a documented search protocol, uniform per-paper notes, and a quality filter on every gap candidate. It is designed to survive a thesis committee asking "how do you know this gap exists".

It does not write the thesis. It produces the literature review and the gap statement. The student writes everything else.

## Quick start

1. Copy or fork this repository.
2. Open `protocol/topic.md`. Fill in your topic, your inclusion emphasis, and the categories you expect to see in the literature.
3. Open `protocol/search_queries.md`. Replace the example queries with queries for your topic.
4. Open `protocol/inclusion_criteria.md`. Adjust the inclusion and exclusion criteria for your topic.
5. Run the pipeline stage by stage. After each stage, inspect the output before launching the next.

## Pipeline stages

```
Stage 1  Search          Queries open APIs.       Writes data/candidates_raw.csv
Stage 2  Triage          Classifies abstracts.    Writes data/candidates_triaged.csv
Stage 3  Download        Fetches PDFs.            Writes data/pdfs/ and data/download_log.csv
Stage 4  Deep read       One note per paper.      Writes notes/paper_NNN.md
Stage 5  Synthesis       Reads notes only.        Writes synthesis/gap_matrix.md and gap_candidates.md
Stage 6  Quality filter  Reads gap matrix.        Writes synthesis/indicator_assessment.md and shortlist.md
Stage 7  Positioning     Reads top notes.         Writes synthesis/positioning_statement.md and prisma_flow.md
```

Each stage reads only the artifact written by the previous stage. After stage four, no later stage opens a PDF. This is the central design constraint and exists to prevent context fatigue in any single agent or any single human reader.

## What this scaffold guarantees

The search protocol is documented and reproducible. Every query executed is logged with timestamp, source, query string, and result identifiers. The PRISMA flow numbers fall out of the log.

The deep read produces uniform notes with a strict schema. Synthesis and quality filtering work on the notes alone, never on the PDFs.

The quality filter applies seven thesis-quality indicators mechanically. Gaps that survive the filter are defensible.

## What this scaffold does not do

It does not access paywalled databases that require institutional VPN. The student adds those papers manually if needed.

It does not replace the supervisor reading the final positioning statement.

It does not generate a thesis title for you. You bring the topic. The pipeline tests whether the topic is viable.

## Repository layout

```
protocol/
  topic.md               Active topic and category list. Fill in first.
  search_queries.md      Query bank for the active topic.
  inclusion_criteria.md  PRISMA inclusion and exclusion rules.
  note_schema.md         Strict schema for stage 4 deep-read notes.
  indicator_rubric.md    Seven thesis quality indicators.

agents/
  01_search.md           Stage 1 procedure.
  02_triage.md           Stage 2 procedure.
  03_download.md         Stage 3 procedure.
  04_deepread.md         Stage 4 procedure.
  05_synthesis.md        Stage 5 procedure.
  06_quality_filter.md   Stage 6 procedure.
  07_positioning.md      Stage 7 procedure.

scripts/
  run_search.py          Stage 1 helper. Standalone, no AI required.
  download_pdfs.py       Stage 3 helper. Standalone, no AI required.
  validate_notes.py      Stage 4 helper. Validates notes against the schema.
  split_for_triage.py    Optional helper. Splits raw CSV into batches.
  merge_triage.py        Optional helper. Merges triaged batches.
  build_bibliography.py  Optional helper. Generates sources.md and sources.bib.

data/                    Generated artifacts. Empty in the template.
notes/                   Per-paper notes. Empty in the template.
synthesis/               Synthesis artifacts. Empty in the template.

AGENTS.md                Pipeline overview and operating rules. Read by AI agents.
CLAUDE.md                Compatibility shim that points at AGENTS.md.
Makefile                 Stage runners and by-hand checklists.
```

## Tooling notes

The Python helper scripts use only `requests`, `feedparser`, and `pyyaml`. Install with `pip install requests feedparser pyyaml`. The scripts are runnable standalone without any AI tool.

Optional: `scripts/md_to_docx.py` converts any Markdown file into a valid Word document (`.docx`). It uses only the Python standard library, so no extra install is needed. Run `make docx IN=path/to/file.md` (optionally `OUT=path/to/file.docx`). Use this whenever you need a Word document: writing Markdown or plain text to a `*.docx` file produces a corrupt document that Word refuses to open.

The agent definitions in `agents/` are markdown files. They make no assumption about which AI you use. Where parallelism matters (stage 4), the file says so and gives a sequential fallback.

## License and attribution

This scaffold is shared as a template for thesis students. Adapt it freely for your own work. Acknowledgement is appreciated, not required.
