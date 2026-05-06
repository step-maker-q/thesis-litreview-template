# Stage 4. Deep Read

## Role

Read every downloaded paper and produce one structured note per paper. The notes are the only artifact synthesis at stage five will read.

This stage is the most expensive in any execution mode. If you have an agentic AI tool, this is where parallelism pays off. If you are running by hand, this is where most of the time goes.

## Inputs

```
data/candidates_triaged.csv
data/pdfs/paper_NNN.pdf
protocol/note_schema.md
protocol/topic.md
```

## Outputs

```
notes/paper_NNN.md  (one per paper successfully read)
data/deep_read_log.csv
```

## Procedure (agentic AI mode)

The orchestrator reads `data/candidates_triaged.csv` and filters to papers where the corresponding `data/pdfs/paper_NNN.pdf` exists. Call this set the read queue.

Partition the queue into batches. The recommended split depends on your harness's parallel-task primitive (Claude Code's Task tool, OpenCode's sub-agents, Aider's `/run`, or any other). Six to twelve parallel sub-tasks works well for queues of 50 to 100 papers. For queues smaller than thirty, four parallel sub-tasks. For queues smaller than twelve, run sequentially.

The helper `python scripts/split_for_deepread.py --num-batches 12` writes one paper-id list per batch to `data/deepread_batches/batch_NN.txt`. The split balances papers across batches.

Dispatch one sub-task per batch. Each sub-task receives: the list of paper_ids in its batch, the path to `protocol/note_schema.md`, and the topic from `protocol/topic.md`. Each sub-task runs the per-paper procedure below.

Wait for all sub-tasks to complete. Run `python scripts/validate_notes.py`. For any note that fails validation, dispatch a single-paper sub-task to redo it with the validation error as additional input.

Write `data/deep_read_log.csv` recording: paper_id, batch, status, word_count, validation_status, errors.

### Per-paper procedure (sub-task)

For each paper_id in your list:

1. Open `data/pdfs/paper_NNN.pdf`. Read the full text. Focus on abstract, introduction, methodology, evaluation, and conclusion. The related work section is read for context but is not summarized in the note.

2. Construct the YAML frontmatter following `protocol/note_schema.md`. Fill every required field. Use enumerated values where the schema constrains them. Booleans are `true` or `false`, lowercase, no quotes.

3. Write the markdown body following the section order in the schema. Six sections in fixed order. Each section is one to four paragraphs of synthesized prose. Do not quote the paper. Do not copy paragraphs. State everything in your own words.

4. Pay particular attention to the `ground_truth` block. The thesis depends on detecting circular ground truth. If the authors construct their own evaluation data without external anchor, set `external` to false and `self_constructed_ground_truth` to true under `quality_flags`.

5. Pay particular attention to the `gaps_opened` body section. Write three to six specific gap statements per paper. Each gap is one sentence describing what the paper leaves unexamined. Generic gaps like "more work needed" are unacceptable. Specific gaps name the unexamined dimension.

6. Save to `notes/paper_NNN.md`.

7. Reset working context between papers. Earlier papers in the batch must not influence the framing of later papers.

## Procedure (single-shot LLM mode)

For each paper:

1. Upload the PDF to the chat (most modern chat LLMs accept PDF attachments).
2. Paste this agent file and `protocol/note_schema.md`.
3. Ask the LLM to produce the note as a complete file (frontmatter plus body) ready to save to `notes/paper_NNN.md`.
4. Save the response.
5. Run `python scripts/validate_notes.py` after every five to ten notes. Address validation errors before continuing.

LLMs without document upload can still produce a note from a copy-pasted abstract plus introduction plus conclusion, at lower quality. Mark such notes with `relevance_to_topic: peripheral` and a comment in the body explaining the partial read.

## Procedure (by hand)

Read each PDF. For each paper, fill the template at the end of this file and save it as `notes/paper_NNN.md`.

Sequencing tips:

- Read in tiers. Start with papers labelled `core` relevance during triage. Their notes set the framing. Adjacent papers come second. Peripheral papers come last and may be skimmed.
- Do not read in CSV order. Order by relevance.
- Reset between papers. Take a short break between notes. Do not let the previous paper's framing leak into the next one.
- After every ten notes, run `python scripts/validate_notes.py` to catch schema drift early.

## Schema enforcement

The validator checks every note. Required frontmatter keys must be present and non-empty. Enumerated fields must use values from the allowed set. Body sections must all be present in the correct order. Notes that fail validation are corrected before stage five begins.

## Anti-context-fatigue rules

Each sub-task in agentic mode reads at most fifteen papers. Each paper is processed independently. Working context is reset between papers within a batch. The orchestrator never reads PDFs. The orchestrator only reads the deep read log and the validation results.

After stage four completes, no later stage opens a PDF. Stage five reads notes only. Stage six reads the gap matrix only. Stage seven reads the assessment and the top-relevance notes only.

## Stop conditions

Stage four stops when every paper in the read queue has a validated note in `notes/`, or the orchestrator has documented why a paper could not be processed (corrupted PDF, unreadable language, OCR failure on a scanned image-only PDF).

Report total notes written, total validation passes, total validation failures resolved, and total papers skipped to the user.

## Quality check before stage five

Spot-check five randomly selected notes. Confirm each has substantive content in the gaps_opened section, has correctly identified the ground truth source, and is between 600 and 1200 words. If spot-checked notes are shallow, redo those papers and consider whether the procedure prompts need tightening.

## By-hand template

Copy the block below into a new file at `notes/paper_NNN.md`. Replace `NNN`, fill the frontmatter, and write the six body sections.

```markdown
---
paper_id: "NNN"
title: ""
authors: []
year: 0
venue: ""
doi: ""
arxiv_id: ""
url: ""
pdf_path: "data/pdfs/paper_NNN.pdf"
read_date: "YYYY-MM-DD"

category: []

method:
  family: ""
  specific: ""
  inputs: []

ground_truth:
  source: ""
  external: false
  case_count: 0
  reproducible: false

evaluation:
  metrics: []
  baseline_compared: false
  has_uncertainty_quantification: false

claims:
  primary_contribution: ""
  novelty_strength: ""

limitations_authors_state: []

quality_flags:
  self_constructed_ground_truth: false
  comparison_table_only: false
  hobby_project_scale: false
  predictable_outcome: false

relevance:
  relevance_to_topic: ""
  must_cite: false
---

## Problem statement

What problem does the paper address. Two to three sentences in the authors' own framing.

## Method summary

How does the paper solve the problem. Cover input, model or technique, and output. Avoid quoting.

## Ground truth and evaluation

Describe the data used for evaluation. Identify whether the ground truth is external or self-constructed. State the case count and the metrics reported.

## Stated limitations

Summarize the limitations the authors acknowledge.

## Gaps this paper opens

Three to six specific gap statements. Each is one sentence in the form "the paper does not address X" or "the paper restricts itself to Y, leaving Z unexamined". Generic statements are not acceptable.

## Relevance to the thesis topic

Two to three sentences. State how this paper relates to the active topic. State whether the thesis must cite this paper and why.
```
