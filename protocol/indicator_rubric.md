# Quality Indicator Rubric

Seven indicators applied at stage six to every gap candidate. Each indicator returns one of three values. PASS, PARTIAL, or FAIL. Each verdict carries a one-line justification. A gap with any FAIL is rejected. A gap with three or more PARTIAL ratings is returned to stage five for refinement.

These indicators are field-agnostic. They apply to any empirical thesis. The thresholds are calibrated for an MSc thesis. For a BSc thesis, halve the literature volume thresholds in indicator 2 and relax indicator 7.

## Indicator 1. Demonstrated gap

The gap must be demonstrated through a documented search protocol. Asserting a gap without evidence is grounds for rejection.

```
indicator_id: 1
name: demonstrated_gap
PASS: The gap is supported by a search of at least three databases with documented queries and at least 50 included papers, and the gap maps to an empty or sparse cell in the gap matrix.
PARTIAL: The gap is supported by the search but the matrix cell has 1 to 2 papers that partially address it.
FAIL: The gap is asserted in prose with no search support, or the matrix cell has 3 or more papers that already address the question.
```

## Indicator 2. Literature volume matches gap type

The literature collection must match the scope of the proposed gap. Thumb values: 50 sources for an MSc, 30 sources for a BSc.

```
indicator_id: 2
name: literature_volume
PASS: At least 50 included papers, with at least 15 of them directly relevant to the proposed gap.
PARTIAL: 30 to 49 included papers, or fewer than 15 directly relevant.
FAIL: Fewer than 30 included papers, or fewer than 5 directly relevant.
```

## Indicator 3. Scientific value

The gap must produce knowledge that was previously unknown. Predictable outcomes are not research. Comparison tables are not knowledge.

```
indicator_id: 3
name: scientific_value
PASS: The research question has a non-trivial answer space and the outcome is genuinely uncertain in advance, with at least one plausible negative result that would change the field's understanding.
PARTIAL: The outcome is partially uncertain but the most likely result is already known to practitioners.
FAIL: The outcome is predictable, or the proposed contribution is a comparison table of existing methods on existing benchmarks.
```

## Indicator 4. Quantifiable results with external validation

Results must be quantifiable. Validation must come from outside the system being evaluated.

```
indicator_id: 4
name: external_validation
PASS: The proposal names a specific external ground truth source with a concrete case count of at least 30 reproducible items, and the metrics are well-defined numerical scores with confidence intervals.
PARTIAL: External validation is named but case count is below 30, or metrics are defined without uncertainty quantification.
FAIL: Ground truth is constructed by the student during the thesis without external anchor, or the metrics are qualitative.
```

## Indicator 5. Falsifiability and reproducibility

The research question must admit a clear answer that could be wrong. The methodology must be reproducible by an independent researcher.

```
indicator_id: 5
name: falsifiability_reproducibility
PASS: The research question is stated in the form "does X outperform Y under condition Z" or equivalent, with explicit success and failure criteria, and the data, code, and evaluation protocol are committed to be released.
PARTIAL: The question is falsifiable but reproducibility commitments are vague.
FAIL: The question cannot be falsified, or no reproducibility plan exists.
```

## Indicator 6. Methodology fit

The methodology must fit the research question. Self-constructed ground truth is circular when the same student constructs both the data and the model that learns from it.

```
indicator_id: 6
name: methodology_fit
PASS: The methodology is appropriate for the question, the ground truth is independent of the student's model construction, and any synthetic data is justified and validated against real cases.
PARTIAL: The methodology fits but contains a circularity risk that can be mitigated through a defined external check.
FAIL: The student trains and evaluates on data they themselves labelled or generated without an independent reference, or the methodology cannot answer the stated question.
```

## Indicator 7. Hobby project test

If the proposed work is doable on a Saturday afternoon, it is not a thesis. The required engineering and scientific effort must be substantial.

```
indicator_id: 7
name: hobby_project_test
PASS: The work requires sustained engineering effort over months, includes non-trivial system construction, and integrates at least two distinct technical components.
PARTIAL: The work is substantial but a competent practitioner could complete it in two to three weeks of focused effort.
FAIL: The work could be completed in a single afternoon by an experienced practitioner, or it amounts to running an existing tool on an existing dataset.
```

## Output format for stage six

Stage six produces `synthesis/indicator_assessment.md` with one section per gap candidate. Each section contains a table of seven rows, one per indicator, with columns for indicator name, verdict, and justification. The section ends with an overall verdict of `accept`, `refine`, or `reject` and a recommendation paragraph.
