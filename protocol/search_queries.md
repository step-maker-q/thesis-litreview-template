# Search Queries

Replace the example queries with queries for your topic before running stage one. The active topic is configured in `protocol/topic.md`.

## Search sources

Three open APIs are queried at stage one. Paywalled databases are excluded from the automated pipeline. The student adds results from institutional databases manually if needed.

```
sources:
  - name: arxiv
    api: http://export.arxiv.org/api/query
    rate_limit: 1 request per 3 seconds
  - name: openalex
    api: https://api.openalex.org/works
    rate_limit: 10 requests per second
  - name: semantic_scholar
    api: https://api.semanticscholar.org/graph/v1/paper/search
    rate_limit: 1 request per second without API key
```

If you have institutional access to IEEE Xplore, ACM Digital Library, ScienceDirect, SpringerLink, or PubMed, run those searches separately and add the results under "Manual additions" below.

## Query bank

List eight to twelve queries that cover your topic. Each query runs against all three sources. Queries are short search-engine-style strings, not full sentences.

A good query bank includes queries at three levels of specificity:
- two or three queries that are tight to the exact topic phrasing
- four or five queries that cover the topic from different angles or use synonym terminology
- two or three broader queries that catch adjacent or transferable methodology

Replace the example below.

```
example topic core query
example topic synonym query
example topic alternative phrasing
example topic methodology angle one
example topic methodology angle two
example topic adjacent domain transfer
example topic recent technique application
example topic benchmark or dataset
```

## Query execution rules

Each query string runs against each source independently. Result limits per source per query: 50 results from arxiv, 100 from openalex, 100 from semantic_scholar.

For each result, capture: title, authors, year, venue, abstract, DOI, source_database, pdf_url, source_query.

Deduplication uses normalized DOI as primary key. Title fuzzy match (Jaccard over tokenized lowercased titles, threshold 0.85) is the secondary deduplication signal for results without DOI.

## Manual additions

The student lists papers that the automated search may miss. These are typically:
- The historical anchor paper (the original work that defined the problem your thesis addresses).
- The closest direct prior work that you already know about from your supervisor or your reading.
- Industry research notes that do not appear on arXiv or in OpenAlex.
- Papers behind paywalls that you have access to through your institution.

Each manual addition is one entry. The format mirrors what the search returns so the rest of the pipeline does not need a special path.

```
- title: The original paper that defined the problem in your field
  authors: Author One, Author Two, Author Three
  year: YYYY
  venue: Conference or journal name
  doi: 10.NNNN/example
  url: https://example.org/paper
  reason: historical anchor for the topic
```

Manual additions are appended to `data/candidates_raw.csv` with `source_database: manual_addition` so PRISMA accounting can separate them from API results.

## Output

Stage one writes `data/candidates_raw.csv` with one row per result and `data/search_log.jsonl` with one line per query executed.
