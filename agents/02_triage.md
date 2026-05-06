# Stage 2. Triage

## Role

Read titles and abstracts from the raw candidate list and classify each paper as include, exclude, or maybe. Assign a paper_id to every included and maybe-paper.

## Inputs

```
data/candidates_raw.csv
protocol/topic.md
protocol/inclusion_criteria.md
```

## Outputs

```
data/candidates_triaged.csv
data/triage_summary.md
```

## Procedure (agentic AI mode)

Read the topic file and the inclusion and exclusion criteria. Hold both in working context for the duration of stage two.

If your harness supports parallel sub-tasks and the candidate count is above 200, split the work into batches with `python scripts/split_for_triage.py --num-batches 8`. Each batch is a CSV at `data/triage_batches/batch_NN.csv`. Dispatch one sub-task per batch, each running the per-row procedure below. Merge with `python scripts/merge_triage.py`.

If your harness has no parallel primitive, or the candidate count is below 200, process the rows sequentially in one pass.

Per-row procedure:

For each row, evaluate the title and abstract against the criteria. Apply inclusion criteria first. If any inclusion criterion fails clearly based on the abstract alone, label the paper `exclude` with the failing criterion as the reason.

Apply exclusion criteria second. If any exclusion criterion clearly applies, label the paper `exclude` with the criterion as the reason.

If the abstract is ambiguous and full text would resolve the question, label the paper `maybe` and record the specific question that needs full text to answer.

If the paper passes all checks, label it `include`.

Apply any topic-specific decision rules listed in `protocol/inclusion_criteria.md`.

Write `data/candidates_triaged.csv` containing all rows from the raw file plus three additional columns: triage_label, triage_reason, paper_id. Assign paper_id starting at "001" in row order. Skip excluded papers in numbering. Both include and maybe receive IDs.

Write `data/triage_summary.md` with: total raw count, counts per label, top five exclusion reasons, sample of ten included papers with one-line justification, and a warning if include count falls outside the target range from `protocol/topic.md`.

## Procedure (single-shot LLM mode)

Use the helper `python scripts/split_for_triage.py --num-batches 8` to split the input into manageable chunks.

For each batch, paste the following into the chat: this agent file, the topic file, the inclusion criteria file, and the batch CSV. Ask the LLM to return a CSV with the columns `row_index, triage_label, triage_reason`. Save the response to `data/triage_batches/batch_NN_triaged.csv`.

After all batches are returned, run `python scripts/merge_triage.py` to assemble `data/candidates_triaged.csv` and `data/triage_summary.md`.

## Procedure (by hand)

Open `data/candidates_raw.csv` in a spreadsheet. Add three new columns: `triage_label`, `triage_reason`, `paper_id`.

Go row by row. Do not over-think individual rows. If the abstract does not give you enough information to decide quickly, label `maybe` and move on. The decision tree:

1. Read title.
2. If title clearly out of scope, label exclude. Move on.
3. If title plausibly in scope, read abstract.
4. Apply the four inclusion criteria from `protocol/inclusion_criteria.md`. Any clear fail means exclude.
5. Apply the exclusion criteria. Any clear hit means exclude.
6. If you cannot decide from the abstract, label maybe.
7. Otherwise label include.

Record a one-sentence reason in `triage_reason` for every decision. The PRISMA diagram needs the exclusion reasons to be specific.

After triaging the whole file, sort by `triage_label` (include and maybe at the top, exclude below). Number the include and maybe rows in the order they appear, "001", "002", and so on, in the `paper_id` column. Leave excluded rows with empty `paper_id`.

Save as `data/candidates_triaged.csv`.

Write `data/triage_summary.md` by hand:

```markdown
# Triage summary

## Total raw count
NNN candidates evaluated.

## Label distribution
- include: NN
- maybe: NN
- exclude: NN

## Top exclusion reasons
- NN: <reason>
- NN: <reason>

## Warning
[State whether the include count falls outside the target range from protocol/topic.md.]

## Sample of included papers
- paper_001 (YYYY, Venue). Title. Reason: ...
- paper_002 (YYYY, Venue). Title. Reason: ...
```

## Decision rule template

The default decision rules in `protocol/inclusion_criteria.md` cover most cases. Add project-specific rules to that file as you encounter edge cases. Common patterns:

If the abstract names the topic explicitly using the same terminology as the topic file, include without further evaluation.

If the paper proposes a methodology in an adjacent domain that plausibly transfers to the active topic, include with reason "methodology transfer".

If the paper is a survey older than three years, exclude with reason "survey out of date".

## Anti-context-fatigue rule

You do not download PDFs. You do not read full texts. You operate on the abstract alone. If the abstract does not give you enough information to decide, label `maybe` and move on. Over-thinking individual rows at this stage costs more than it saves, since the maybe-label is the safety net.

## Stop conditions

Stage two stops when every row in `data/candidates_raw.csv` has a triage label and `data/candidates_triaged.csv` and `data/triage_summary.md` have been written.

If the include count is below the minimum from `protocol/topic.md`, report this to the user. The likely cause is overly narrow search queries at stage one. The user may rerun stage one with expanded queries before proceeding.

If the include count is above twice the target, report this to the user. The likely cause is overly broad inclusion criteria. The user may tighten the criteria and rerun stage two.
