# Stage 1. Search

## Role

Execute the documented search protocol against three open APIs, capture every result, and write a deduplicated candidate list. Produce no judgments at this stage. Triage happens at stage two.

## Inputs

```
protocol/topic.md
protocol/search_queries.md
```

## Outputs

```
data/candidates_raw.csv
data/search_log.jsonl
```

## Procedure (agentic AI mode)

Read `protocol/topic.md` and `protocol/search_queries.md`. Hold the query bank and the contact email in working context.

Run `python scripts/run_search.py --email "$contact_email"` from the repository root. The script handles all three APIs, rate limiting, pagination, and deduplication. It writes `data/candidates_raw.csv` and appends to `data/search_log.jsonl`.

If you prefer to execute the searches yourself rather than running the script, query each API once per query string and write the same CSV columns. The script is the reference implementation.

After the script completes, append the manual additions from `protocol/search_queries.md` to the CSV. The helper `python scripts/append_manual_additions.py` does this from a YAML block in the search queries file. Mark each manual row with `source_database: manual_addition`.

Report the total raw row count, the count after deduplication, and any API errors logged to `data/search_log.jsonl` to the user before stage two begins.

## Procedure (single-shot LLM mode)

The single-shot LLM cannot make HTTP calls. Run `python scripts/run_search.py` yourself outside the chat. The LLM has no role at stage one. Skip to stage two.

## Procedure (by hand)

You can execute stage one entirely in a browser if Python is unavailable.

For each query in `protocol/search_queries.md`, open the three APIs in a browser:

```
arxiv.org/search/?query=<query>&start=0
openalex.org/works?search=<query>
semanticscholar.org/search?q=<query>
```

For each result on the first one or two pages, copy title, authors, year, venue, abstract, DOI, and URL into a spreadsheet with the columns named in the script reference below. Save as `data/candidates_raw.csv`.

After all queries are entered, deduplicate by DOI in the spreadsheet. For rows without DOI, scan the title list and remove obvious duplicates by inspection. The Jaccard threshold of 0.85 used by the script roughly corresponds to "the titles share most words ignoring word order".

Append the manual additions block from `protocol/search_queries.md` to the bottom of the CSV. Mark `source_database: manual_addition` on those rows.

Append one line per query you ran to `data/search_log.jsonl` with the following fields, even if you did the work in a browser:

```json
{"timestamp": "YYYY-MM-DDTHH:MM:SSZ", "source": "arxiv|openalex|semantic_scholar", "query": "the query string", "result_count": N, "ids": ["id1", "id2"]}
```

The PRISMA flow at stage seven needs this log. If you skip the log, you cannot produce a defensible PRISMA diagram.

## CSV columns reference

```
paper_id, title, authors, year, venue, abstract, doi, arxiv_id, url, pdf_url, source_database, source_query
```

`paper_id` is left empty at this stage. IDs are assigned at stage two during triage based on the order of inclusion.

## Stop conditions

Stage one stops when all queries in the active bank have been executed against all three sources, deduplication has run, manual additions are appended, and `data/candidates_raw.csv` exists.

Expected raw result count is 200 to 500 rows after deduplication. Counts below 100 indicate the queries are too narrow. Counts above 800 indicate the queries are too broad. In either case, report the count to the user before stage two begins.

## Anti-context-fatigue rule

You do not read PDFs at this stage. You do not classify papers. You do not produce gap statements. The only task is to execute queries and write the candidate file.
