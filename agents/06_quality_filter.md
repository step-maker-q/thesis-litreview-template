# Stage 6. Quality Filter

## Role

Apply the seven thesis quality indicators to every gap candidate from stage five. Produce a verdict per indicator and an overall verdict per candidate. Produce a ranked shortlist of candidates that pass all indicators.

## Inputs

```
synthesis/gap_candidates.md
synthesis/gap_matrix.md
protocol/indicator_rubric.md
notes/paper_NNN.md   (read selectively when verifying claims about prior work)
data/triage_summary.md
```

## Outputs

```
synthesis/indicator_assessment.md
synthesis/shortlist.md
```

## Procedure (agentic AI mode)

Read `protocol/indicator_rubric.md` and hold the seven indicator definitions in active context.

Read `synthesis/gap_candidates.md`. For each candidate, run the assessment below.

For each of the seven indicators, evaluate the candidate against the rubric and assign one of PASS, PARTIAL, or FAIL. Write a one-line justification per indicator.

**Indicator 1, demonstrated gap.** Verify that the candidate's evidence section names specific papers from the notes and that the matrix cell or cross-paper observation is genuinely sparse. If the candidate cites three or more papers that already address the question, the gap is not demonstrated and this indicator fails.

**Indicator 2, literature volume.** Cross-check against `data/triage_summary.md` for total inclusion count. Cross-check against `synthesis/gap_matrix.md` for the count of papers directly relevant to the candidate's category. PASS requires 50 plus included and 15 plus directly relevant for an MSc thesis.

**Indicator 3, scientific value.** Read the research question. Ask whether a competent practitioner could predict the outcome before running the experiment. If yes, fail. If a comparison-table contribution is the primary deliverable, fail. If the outcome space is genuinely uncertain and a negative result would change the field's understanding, pass.

**Indicator 4, external validation.** Check the candidate's external validation source. If the source is a named public dataset, public registry, public disclosure set, or named third-party benchmark with at least 30 reproducible cases, pass. If the source is constructed by the student during the thesis with no external anchor, fail.

**Indicator 5, falsifiability and reproducibility.** Confirm the research question is stated in falsifiable form with explicit success and failure criteria. Confirm the candidate commits to releasing data, code, and evaluation protocol. PASS requires both.

**Indicator 6, methodology fit.** The hardest check. Read the candidate's methodology paragraph. Identify circularity. If the same person constructs the data, trains the model, and evaluates on the data they constructed, fail. If synthetic data is used without an external real-world validation step, fail. If the methodology has a defined external check, pass or partial depending on the rigor of the check.

**Indicator 7, hobby project test.** Estimate the engineering effort. If the work amounts to running an existing tool on an existing dataset, fail. If a competent practitioner could complete it in a weekend, fail. If the work requires building two or more distinct technical components and integrating them, with sustained effort over months, pass.

For each candidate, compute the overall verdict.

`accept` if all seven indicators are PASS.

`refine` if there are no FAIL ratings and three or fewer PARTIAL ratings.

`reject` if there is any FAIL rating, or four or more PARTIAL ratings.

Write `synthesis/indicator_assessment.md` with one section per candidate. Each section has a header with the candidate title, a table of seven rows (indicator name, verdict, justification), the overall verdict, and a recommendation paragraph. The recommendation either accepts the candidate as-is, names the specific changes needed to upgrade PARTIAL ratings to PASS, or explains why the candidate is not viable.

Write `synthesis/shortlist.md` ranking the accepted candidates and the refinable candidates. The ranking criterion is the strength of indicator 3 (scientific value) breaking ties on indicator 6 (methodology fit). Rejected candidates are listed at the bottom with one-line dismissal reasons.

## Procedure (single-shot LLM mode)

Paste this agent file plus `protocol/indicator_rubric.md` plus `synthesis/gap_candidates.md` plus `synthesis/gap_matrix.md` plus `data/triage_summary.md` into the chat. Ask the LLM to produce both output files. The total context fits comfortably in any modern chat LLM since gap candidates and the matrix are short.

Validate the response by spot-checking that each indicator verdict has a non-empty justification and that the overall verdict logic was applied correctly.

## Procedure (by hand)

Open `synthesis/gap_candidates.md` and `protocol/indicator_rubric.md` side by side.

For each candidate, draw a seven-row table. For each indicator, read the rubric definition and decide PASS, PARTIAL, or FAIL. Write the one-line justification immediately. Do not skip the justification. Justifications you cannot write usually mean the verdict is wrong.

After all seven indicators are assessed, apply the verdict logic:

- All PASS → accept.
- No FAIL and three or fewer PARTIAL → refine.
- Any FAIL or four plus PARTIAL → reject.

Write the candidate's section into `synthesis/indicator_assessment.md`. Recommendation paragraph names what would need to change to upgrade PARTIAL to PASS, or why the candidate is not viable.

After all candidates are assessed, sort the accepts and refines by the strength of indicator 3 (scientific value), breaking ties on indicator 6 (methodology fit). Write the ranked list to `synthesis/shortlist.md`. Append rejected candidates with one-line dismissal reasons.

## Anti-context-fatigue rules

Read notes only when verifying a specific claim about prior work. Do not reread notes wholesale. The gap matrix and the gap candidates file already aggregate what you need.

Do not modify the gap candidates. If a candidate has a fixable problem, the recommendation paragraph names the fix. The fix is executed at stage five (rerun) or at stage seven if the user instructs.

Do not write the positioning statement. That is stage seven.

## Common failure patterns to watch for

These patterns appear across many topics. Watch for them while assessing.

A candidate proposes "applying $RECENT_TECHNIQUE to $TOPIC". This typically fails indicator 3 (scientific value) because the outcome is partially known. It often fails indicator 6 (methodology fit) because the technique is rarely grounded against external truth.

A candidate proposes "comparing technique A versus technique B on benchmark C". This fails indicator 3 because comparison tables are not knowledge.

A candidate proposes "building a new benchmark for $TOPIC". This may pass on its own merits but rarely sustains an MSc thesis without a methodology contribution attached.

A candidate proposes "transfer learning from $ADJACENT_DOMAIN to $TOPIC". This passes indicator 3 if the transfer behavior is genuinely uncertain. It fails indicator 4 if no external multi-domain benchmark exists.

A candidate uses self-constructed ground truth. This fails indicator 6 unless an external validation step is added.

## Stop conditions

Stage six stops when every gap candidate has a complete assessment, the shortlist is written, and at least one candidate has a verdict of `accept` or `refine`.

If every candidate is rejected, return to stage five with the failure reasons. The synthesis stage generates new candidates that address the specific failure modes.
