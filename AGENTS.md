# Thesis Literature Review Pipeline

This file is the operating contract for any agent (AI or human) running the pipeline. It is referenced by every stage. Read it before running any stage.

## Purpose

Produce a documented and defensible literature review for an MSc or BSc thesis on the topic configured in `protocol/topic.md`. The output of the pipeline must satisfy seven thesis quality indicators stored in `protocol/indicator_rubric.md`. Every gap candidate the pipeline produces is assessed against these indicators before it leaves stage six. A gap that fails any indicator is rejected.

## Architecture

The pipeline runs in seven stages. Each stage reads only structured artifacts written by prior stages. After stage four, no stage re-reads PDFs. This is the central design constraint and exists to prevent context fatigue in any single agent or any single human reader.

```
Stage 1  Search          Queries open APIs.   Writes data/candidates_raw.csv
Stage 2  Triage          Classifies abstracts. Writes data/candidates_triaged.csv
Stage 3  Download        Fetches PDFs.        Writes data/pdfs/ and data/download_log.csv
Stage 4  Deep read       Per-paper notes.     Writes notes/paper_NNN.md
Stage 5  Synthesis       Reads notes only.    Writes synthesis/gap_matrix.md
Stage 6  Quality filter  Reads gap matrix.    Writes synthesis/indicator_assessment.md
Stage 7  Positioning     Reads top notes.     Writes synthesis/positioning_statement.md and prisma_flow.md
```

Each agent has a definition file in `agents/`. The orchestrator (the AI or the student) reads the agent file, executes the work or delegates it, and writes only the named output artifact for that stage.

## Topic configuration

The active topic is defined in `protocol/topic.md`. The student fills this file before stage one runs. The topic determines the query banks, the inclusion criteria emphasis, and the category labels used in the gap matrix.

## Operating rules

Read only the artifact produced by the previous stage. Do not re-read PDFs after stage four. Do not hold more than one paper in working context at any time during stages five through seven.

Every stage produces an artifact at a named path. The next stage reads that path. If the artifact is missing or fails the validation script, stop and report.

Sub-agents may run in parallel only at stage four. Other stages run sequentially because their outputs depend on prior outputs.

When asked a question about a specific paper, read the corresponding note in `notes/`. Do not open the PDF unless the note is incomplete and the question requires content the schema did not capture.

## Running modes

The pipeline supports three execution modes. Mix them per stage.

**Agentic AI mode.** Any agentic coding tool with a parallel-task primitive (Claude Code's Task tool, OpenCode's sub-agents, Aider, Cursor, Codex, Continue, custom orchestrators built on Anthropic or OpenAI APIs). The orchestrator reads the relevant agent file and either runs the work itself or delegates to sub-agents.

**Single-shot LLM mode.** Paste the agent file plus the input artifact into a chat LLM. Write the response to the named output path. Validate. Repeat for the next stage.

**By hand.** Each agent file has a "Run by hand" section. The student opens a browser, runs queries, fills the schema templates, and runs the validation script.

Stage four is the most expensive stage in any mode. Triage carefully at stage two before spending the cost of full reading.

## Writing style for all artifacts

Every output produced by this pipeline follows these rules. The agents enforce them.

No em dashes. No double dashes. No semicolons or colons used as punctuation substitutes. Use periods or commas. Restructure into clear consecutive sentences.

No "X not Y" constructions. No "not X but Y" constructions. Invert into direct attributive form. Example replacement. "The model is fast not accurate" becomes "The model is fast at the cost of accuracy".

Direct, human, concise. No AI voice patterns. No filler phrases. No "it is worth noting", "it should be mentioned", "in conclusion", or similar.

Avoid the rhetorical pattern "They do not do A. They do B." Merge into one consecutive sentence.

Write in the language of the thesis. Translate everything into that language.

## Quality indicators

The seven indicators are stored in machine-readable form in `protocol/indicator_rubric.md`. The quality filter agent applies them mechanically. Each gap candidate receives a PASS, PARTIAL, or FAIL on each indicator with a one-line justification. Gaps with any FAIL are rejected. Gaps with three or more PARTIAL ratings are returned for refinement.

## File handling

PDFs go to `data/pdfs/` named `paper_NNN.pdf` where NNN is the three-digit ID assigned during triage.

Notes go to `notes/` named `paper_NNN.md` matching the PDF ID.

Synthesis artifacts go to `synthesis/`.

Search results, triage decisions, and download logs go to `data/` as CSV.

## Reproducibility

Every search query executed is logged to `data/search_log.jsonl` with timestamp, source, query string, result count, and result identifiers. PRISMA flow numbers are derived from this log at stage seven.

## Failure modes the pipeline catches

A gap that depends on self-constructed ground truth fails indicator six.

A literature collection of fewer than 50 sources for an MSc topic, or fewer than 30 for a BSc topic, triggers a warning at stage two.

A gap that the hobby project test rules out fails indicator seven.

A claimed gap that a paper in `notes/` already addresses fails indicator one and is removed from the shortlist by stage six.
