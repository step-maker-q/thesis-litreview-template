# Inclusion and Exclusion Criteria

PRISMA-style criteria for triage at stage two. Triage operates on title and abstract only. Full-text screening happens at stage four through the deep read.

The defaults below are general. Edit them to match your topic before running stage two. The topic is configured in `protocol/topic.md`.

## Inclusion criteria

A paper is included if all of the following hold.

The paper is published in a peer-reviewed venue, an arXiv preprint, a recognized industry research publication, or a thesis from an accredited university. Blog posts and vendor marketing pages are excluded at stage two.

The paper addresses the topic configured in `protocol/topic.md` either directly or through a methodology that plausibly transfers to that topic. Paper relevance is assessed against the topic description and the category list.

The paper proposes a method, presents an empirical evaluation, or contributes a benchmark or dataset. Pure surveys are included only if they are recent (within the last three years).

The publication year is within the time window stated in `protocol/topic.md`. Papers older than the window are excluded unless they are listed in the manual additions block of `protocol/search_queries.md`.

The paper is in a language the student can read.

## Exclusion criteria

A paper is excluded if any of the following hold.

The paper addresses a different problem class with no transfer to the active topic. The triage decision records what makes the transfer implausible.

The paper is a duplicate of an already included paper, identified by DOI or fuzzy title match.

The paper is a vendor white paper or marketing piece without methodology disclosure.

The paper is a tutorial, a textbook chapter, or a workshop poster without empirical content.

## Triage decision values

Each candidate receives one of three labels.

`include` means the paper passes all inclusion criteria and fails no exclusion criterion. It proceeds to stage three for download.

`exclude` means the paper fails at least one exclusion criterion or fails an inclusion criterion that cannot be remedied at full text. The reason is recorded.

`maybe` means the abstract is ambiguous and full text is needed to decide. Maybe-papers are downloaded at stage three and triaged again at the start of stage four. A maybe paper that fails review at stage four is moved to `exclude` with the reason recorded.

## Topic-specific decision rules

This section lists the project-specific rules that resolve common edge cases. Add rules as you encounter them during your first pass through stage two. Each rule has the form `if <signal> then <decision>` with a short justification.

The defaults below cover the kinds of edge cases that arise on most thesis topics. Edit, add, or remove as needed.

```
- if: the abstract names the topic explicitly using the same terminology as protocol/topic.md
  then: include without further evaluation

- if: the paper proposes a methodology in an adjacent domain that plausibly transfers to the active topic
  then: include with reason "methodology transfer"

- if: the paper is a survey published more than three years ago
  then: exclude with reason "survey out of date"

- if: the abstract is mostly empty or boilerplate
  then: maybe with reason "abstract insufficient to decide"
```

## Target counts

The target inclusion count comes from `protocol/topic.md`. If stage two produces fewer than the minimum, the search queries are insufficient and stage one is rerun with expanded query banks. If stage two produces more than twice the target, the inclusion criteria are tightened by raising the relevance threshold.

## Recording format

Triage decisions are written to `data/candidates_triaged.csv` with the columns from `data/candidates_raw.csv` plus three additional columns. `triage_label` is one of `include`, `exclude`, `maybe`. `triage_reason` is a short justification of one to two sentences. `paper_id` is a three-digit ID assigned to included and maybe-papers in the order of triage.
