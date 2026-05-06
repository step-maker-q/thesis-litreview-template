# Stage 7. Positioning

## Role

Produce the final two artifacts that make the thesis defensible. A one-page positioning statement against the strongest competitor papers, and a PRISMA flow diagram with the search numbers.

## Inputs

```
synthesis/shortlist.md
synthesis/indicator_assessment.md
synthesis/gap_matrix.md
notes/paper_NNN.md      (only the top five competitor papers)
data/search_log.jsonl
data/triage_summary.md
data/download_log.csv
data/deep_read_log.csv
protocol/topic.md
```

## Outputs

```
synthesis/positioning_statement.md
synthesis/prisma_flow.md
```

## Procedure for the positioning statement (any mode)

Read `synthesis/shortlist.md`. Identify the top-ranked candidate. If the user has indicated a preferred candidate from the shortlist, use that one. Otherwise use rank one.

For the selected candidate, identify the top five competitor papers from the gap matrix. Competitors are papers that occupy the same category and the same or adjacent method family.

Read the notes for these five competitors. Hold them in active context for the writing of the statement. Do not read more than five notes at this stage.

Write `synthesis/positioning_statement.md` with the following structure.

```markdown
# Positioning Statement

## Thesis topic

State the proposed thesis title and the core research question in two sentences.

## Field state

One paragraph summarizing where the field stands as of the search execution date. Reference at least three notes by paper_id without long quotation.

## Closest prior work

For each of the five competitor papers, write one paragraph. State what the paper does. State what it does not do that the thesis will do. The paragraph names the paper by author and year and references it by paper_id for traceability.

## Gap statement

State the gap in one paragraph. The gap must be supported by the prior section. The reader must be able to verify that the named competitors do not close the gap.

## Research question

State the falsifiable research question. State the success criterion and the failure criterion explicitly.

## External validation source

Name the specific source of ground truth. State the case count target. State why this source is independent of the student's own construction.

## Methodology overview

Three to five sentences on the methodology. Cover input, model, output, and evaluation protocol. Avoid implementation detail at this level.

## Why this is not a hobby project

Two to three sentences on the engineering scope and the integration of distinct technical components.

## Indicator assessment summary

A short table with the seven indicators and the candidate's verdict on each. This table is copied from `synthesis/indicator_assessment.md`.
```

The statement is one page when rendered. Target 700 to 1000 words excluding the indicator table. The student delivers this to the supervisor as the proposal cover document.

## Procedure for the PRISMA flow (any mode)

Read `data/search_log.jsonl` and count.

**Records identified through database searching.** Sum the raw result counts across all queries and all sources before deduplication.

**Records after duplicates removed.** The count of rows in `data/candidates_raw.csv` after deduplication.

**Records screened.** Same as the previous count.

**Records excluded at title and abstract screening.** Count of rows with triage_label `exclude` in `data/candidates_triaged.csv`. Break down by exclusion reason from the triage_reason column.

**Full-text articles assessed for eligibility.** Count of rows with triage_label `include` or `maybe`.

**Full-text articles excluded with reasons.** Count of rows where the deep read note has `relevance_to_topic: peripheral` or where the paper was abandoned at stage four. Break down by reason.

**Studies included in qualitative synthesis.** Count of notes in `notes/` that contributed to the gap matrix.

**Manual additions.** Count of rows where `source_database: manual_addition`.

Write `synthesis/prisma_flow.md` containing:

A textual PRISMA flow at four levels (identification, screening, eligibility, included) with the numbers above.

A mermaid diagram or a graphviz dot specification that the student can render for the thesis.

A one-paragraph methodology note describing the search process for inclusion in the thesis methodology section. This paragraph is in finished prose, ready to drop into the thesis.

## Procedure (by hand)

The structure above is the procedure. Open the input files, copy the relevant numbers, write the markdown. The writing is the contribution. Do not delegate the prose to a chat LLM that has not read the notes for the five competitors. The competitors must be read first-hand for the closest-prior-work paragraphs to be defensible.

If you are using a chat LLM as a writing aid: paste the five competitor notes plus the selected candidate's section from `synthesis/indicator_assessment.md` plus this agent file. Ask the LLM to produce a draft. Edit the draft against the notes to remove hallucinated claims about the competitors. The student is responsible for every claim in the final document.

## Anti-context-fatigue rules

Read notes only for the top five competitors. Do not reread the full notes corpus. The shortlist and the indicator assessment already aggregate what you need.

Do not regenerate gap candidates. The accepted candidate from the shortlist is the input.

Do not run the seven indicators again. The assessment is already done at stage six. Copy the table.

## Stop conditions

Stage seven stops when the positioning statement and the PRISMA flow are written, the indicator table is included in the statement, and the prose methodology paragraph is finished.

The positioning statement is the deliverable to the supervisor. The PRISMA flow is the deliverable for the thesis methodology section. Both are required for the proposal to proceed.
