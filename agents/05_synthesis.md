# Stage 5. Synthesis

## Role

Read every note in `notes/` and produce a gap matrix that maps the literature against topic categories and method families. From the empty and sparse cells of the matrix, propose gap candidates for stage six to assess.

## Inputs

```
notes/paper_NNN.md   (all notes from stage four)
protocol/topic.md
data/triage_summary.md
```

## Outputs

```
synthesis/gap_matrix.md
synthesis/gap_candidates.md
```

## Procedure (agentic AI mode)

Read every note in `notes/`. Hold only the frontmatter and the `gaps_opened` and `relevance_to_thesis_topic` sections in active context. The other body sections are present in the notes for reference but do not need to be reread for synthesis.

Construct the gap matrix as a two-dimensional table.

Rows are topic categories drawn from the `category` field across all notes. Use the categories defined in `protocol/topic.md`. Add `other` for papers that do not fit any named category.

Columns are method families drawn from the `method.family` field, optionally subdivided by `method.inputs` if the input modality matters for your topic.

Cell values are lists of paper_ids that address that combination, with a count.

Write the matrix to `synthesis/gap_matrix.md` as a markdown table. Each cell contains the count of papers and the comma-separated paper_ids. Empty cells are marked with a dash.

Below the matrix, identify five categories of gap candidates.

**Empty cells.** Combinations of category and method that no paper in the literature addresses. List each empty cell with a one-sentence note on whether this absence is meaningful or whether the combination is not worth pursuing.

**Sparse cells with one or two papers.** List with paper_ids. Comment on whether the existing papers fully address the combination or leave room.

**Cross-paper gaps.** Gaps that emerge from comparing multiple papers. Examples include external validation gaps where many papers exist but none use external ground truth, transfer learning gaps where every paper trains and evaluates on the same dataset, or temporal gaps where the field has moved on but a class of problems has not been revisited with newer methods.

**Methodological gaps.** Gaps in how the field validates results. Pull these from the `quality_flags.self_constructed_ground_truth` field across notes. Count how many papers in the relevant cells use self-constructed ground truth. If the count is high, this is a methodological gap.

**Domain transfer gaps.** Cases where a methodology has been demonstrated in an adjacent domain but not in the active topic domain.

Write `synthesis/gap_candidates.md` containing five to ten concrete gap candidates. Each candidate has the structure below.

```
### Gap candidate N. Short title

Statement. One sentence describing what the field has not addressed.

Evidence. List of paper_ids that establish the gap is real, with one-line notes on what each does and does not cover.

Research question. A falsifiable question of the form "does X outperform Y under condition Z" or equivalent.

External validation source. A specific named source for ground truth (named public dataset, public registry, named benchmark, named disclosure set), with an estimated case count.

Methodology fit. One to two sentences on why the proposed methodology fits the question and avoids circular ground truth.

Hobby project test. One sentence on why the work cannot be done in a weekend.
```

## Procedure (single-shot LLM mode)

The full notes corpus rarely fits in a single chat context. Two-pass approach:

Pass one. Concatenate the frontmatter blocks of all notes into one file (`scripts/build_bibliography.py` does this as a side effect, the YAML structure is preserved). Paste the concatenation plus this agent file plus `protocol/topic.md` into the chat. Ask the LLM to produce the gap matrix only.

Pass two. For each empty or sparse cell identified in pass one, paste the relevant notes (only the gaps_opened sections of papers in adjacent cells) into a new chat. Ask the LLM to produce one gap candidate per cell using the structure above.

Validate the result by spot-checking that each candidate's evidence section names papers that actually exist in `notes/`.

## Procedure (by hand)

Step 1. Build the matrix.

Open a fresh markdown file at `synthesis/gap_matrix.md`. Write a markdown table with topic categories from `protocol/topic.md` as rows and method families as columns. Add a column for "all methods" and a row for "all categories".

For each note in `notes/`, read only the frontmatter. Find the cell corresponding to the paper's `category` and `method.family`. Append the paper_id to that cell. If the paper has multiple categories, append it to multiple cells.

After processing all notes, count papers per cell. Write the count plus the paper_ids in each cell. Mark empty cells with a dash.

Step 2. Find the gaps.

Empty cells are obvious. Highlight them.

Sparse cells (one or two papers) are next. Read the gaps_opened sections of those papers to confirm they do not actually close the cell.

Cross-paper gaps require reading the gaps_opened sections across many papers and looking for repeated themes. A theme that appears in five plus papers as "the paper does not address X" is a cross-paper gap.

Step 3. Write five to ten candidates using the structure above.

The hardest field is "external validation source". This is where most gap candidates fail at stage six. Name a specific dataset, registry, or public archive. If you cannot name one, the candidate is unlikely to survive indicator 4.

## Anti-context-fatigue rules

Read notes only. Do not open PDFs at this stage. If a note is incomplete, return it to stage four for correction rather than reading the source paper yourself.

Do not write the final positioning statement at this stage. That is stage seven. The only output of stage five is the gap matrix and the gap candidates.

Do not assess the gap candidates against the seven indicators. That is stage six. The only assessment at stage five is whether the gap exists in the literature, not whether it would make a good thesis.

## Quality check before stage six

A gap matrix with no empty cells indicates either the row and column granularity is too coarse, or the literature genuinely covers everything in the active topic. The first is more likely. Refine the granularity (split a category into sub-categories, split a method family by input modality) and reproduce the matrix.

A gap candidates file with fewer than five candidates indicates the matrix is too sparse or the synthesis is too cautious. A file with more than ten candidates indicates the synthesis has not pruned enough. Aim for five to ten well-stated candidates that stage six can assess in a single pass.
