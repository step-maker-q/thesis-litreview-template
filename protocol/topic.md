# Topic configuration

Fill this file before running stage one. Every other stage reads it for context.

## Active topic

State the working title of your thesis in one line. Replace the example.

```
title: A Reproducible Title for the Working Thesis Topic
```

## Topic description

Write three to five sentences. State the problem, the proposed angle, and why the topic matters. This block is read by every stage and frames triage decisions, gap matrix axes, and the positioning statement.

```
description: |
  Replace with a short description of your topic. State the problem the thesis
  addresses, the proposed angle of attack, and what would make the result
  scientifically interesting. Keep it concrete. Avoid framing the topic as
  "applying X to Y" without saying what would be surprising about the result.
```

## Topic categories

The gap matrix at stage five uses these labels as row headers. List the categories you expect to see in the literature for your topic. Five to twelve categories is normal. Too few makes the matrix coarse, too many makes it sparse.

The labels are project-specific. Pick labels that distinguish *what kind of problem* a paper addresses within your topic. Examples by field follow.

For a thesis on machine learning detection of a vulnerability class, categories might be the sub-types of vulnerability and the application surfaces. For a thesis on natural language processing, categories might be the linguistic phenomena addressed. For a thesis on a clinical question, categories might be the patient populations or intervention types.

```
categories:
  - replace_with_category_one
  - replace_with_category_two
  - replace_with_category_three
  - replace_with_category_four
  - replace_with_category_five
  - other
```

Always include `other` as the final category. Papers that do not fit any named category land there.

## Method families

The gap matrix uses these labels as column headers. They name *how* a paper attacks the problem. The defaults below are general and apply to most empirical theses. Edit if your field uses different terminology.

```
method_families:
  - rule_based
  - classical_ml
  - deep_learning
  - llm
  - hybrid
  - formal_methods
  - other
```

## Time window

Default time window for the search. Adjust if your topic has a different historical anchor.

```
year_min: 2018
year_max: present
```

If a foundational older paper exists, list it under "Manual additions" in `protocol/search_queries.md`. Older work is otherwise excluded by the automated search.

## Target literature volume

Thumb values. Adjust if your committee has different expectations.

```
msc_target_includes: 50
msc_minimum_includes: 30
bsc_target_includes: 30
bsc_minimum_includes: 15
```

If stage two produces fewer includes than your minimum, stage one is rerun with expanded query banks. If stage two produces more than twice the target, the inclusion criteria are tightened.

## Contact email

Set the email that goes into the User-Agent header of every API request. Many open APIs require this for politeness.

```
contact_email: REPLACE_WITH_YOUR_EMAIL
```

This email is also used by the Unpaywall API at stage three to find open-access PDFs.
