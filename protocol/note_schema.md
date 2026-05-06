# Note Schema for Deep Read Stage

Every paper read at stage four produces one note file at `notes/paper_NNN.md`. The schema is strict. The validator script `scripts/validate_notes.py` rejects notes with missing required fields. Synthesis at stage five operates on notes alone and depends on the schema being uniform across all papers.

## File structure

The file has YAML frontmatter followed by a markdown body. The frontmatter contains all structured fields. The markdown body contains free-form fields under fixed headings.

## Frontmatter schema

The fields below are required. Enumerated fields list their allowed values inline. The `category` and `method.family` lists pull their allowed values from `protocol/topic.md`. The validator reads the topic file and accepts those values plus the literal string `other`.

```yaml
---
paper_id: "001"
title: ""
authors: []
year: 0
venue: ""
doi: ""
arxiv_id: ""
url: ""
pdf_path: "data/pdfs/paper_001.pdf"
read_date: "YYYY-MM-DD"

category: []           # subset of categories from protocol/topic.md, plus "other"

method:
  family: ""           # one of method_families from protocol/topic.md, plus "other"
  specific: ""         # short string naming the model or tool
  inputs: []           # what the method consumes, e.g. raw text, tabular data, images, time series, traffic logs

ground_truth:
  source: ""           # short label for the ground truth origin, e.g. public_dataset, manual_annotation, expert_review, simulation
  external: false      # boolean. true if the ground truth is independent of the authors' system
  case_count: 0        # number of evaluation instances
  reproducible: false  # boolean. true if the cases can be replicated by another researcher

evaluation:
  metrics: []          # e.g. precision, recall, f1, accuracy, rmse, auroc, bleu, exact_match
  baseline_compared: false           # boolean. true if compared against at least one baseline
  has_uncertainty_quantification: false  # boolean. true if reports confidence intervals or error bars

claims:
  primary_contribution: ""  # one sentence
  novelty_strength: ""      # one of: strong, moderate, incremental, unclear

limitations_authors_state: []  # list of limitations the authors themselves acknowledge

quality_flags:
  self_constructed_ground_truth: false  # true if circular ground truth concern applies
  comparison_table_only: false           # true if the contribution is mainly a comparison of existing methods
  hobby_project_scale: false             # true if the work could be reproduced on a single laptop in a weekend
  predictable_outcome: false             # true if the result was predictable from prior work

relevance:
  relevance_to_topic: ""    # one of: core, adjacent, peripheral
  must_cite: false           # boolean. true if any thesis on the active topic must engage with this paper
---
```

## Markdown body sections

The body has these headings in this order. Each section is one to four paragraphs of prose. No bullet lists in the body.

```
## Problem statement

What problem does the paper address. State it in the authors' own framing in two to three sentences.

## Method summary

How does the paper solve the problem. Cover the input, the model or technique, and the output. Avoid quoting the paper.

## Ground truth and evaluation

Describe the data used for evaluation. Identify whether the ground truth is external or self-constructed. State the case count and the metrics reported.

## Stated limitations

Summarize the limitations the authors acknowledge in the paper.

## Gaps this paper opens

Identify what this paper leaves open. Be specific. Each gap is one sentence in the form "the paper does not address X" or "the paper restricts itself to Y, leaving Z unexamined". Three to six gap statements per paper.

## Relevance to the thesis topic

In two to three sentences, state how this paper relates to the active topic in `protocol/topic.md`. State whether the thesis must cite this paper and why.
```

## Validation

The validator script `scripts/validate_notes.py` checks every note file for: required frontmatter keys present, allowed values for enumerated fields, non-empty body sections, paper_id matches filename. Notes that fail validation are returned to the deep read stage for correction before stage five begins.

## Length target

Each note targets 600 to 1200 words total including frontmatter. Notes longer than 1500 words indicate the reader has copied content from the paper rather than synthesizing. Notes shorter than 400 words indicate the reader has not engaged deeply with the paper.
