#!/usr/bin/env python3
"""
Search execution helper. Stage 1.

Reads queries from protocol/search_queries.md and the contact email from
protocol/topic.md. Runs each query against arXiv, OpenAlex, and Semantic
Scholar with rate limiting. Deduplicates by DOI and by Jaccard title
similarity. Writes data/candidates_raw.csv and data/search_log.jsonl.

Standalone. No AI required. Runnable on any machine with Python 3.10+.

Usage:
    python scripts/run_search.py
    python scripts/run_search.py --email [email protected]
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    import feedparser
except ImportError:
    print("Required packages: requests, feedparser, pyyaml")
    print("Install with: pip install requests feedparser pyyaml")
    sys.exit(2)


ARXIV_API = "http://export.arxiv.org/api/query"
OPENALEX_API = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

USER_AGENT_TEMPLATE = "LitReview/1.0 (mailto:{email})"


def log_query(log_path, source, query, params, result_count, ids):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "query": query,
        "params": {k: v for k, v in params.items() if k != "mailto"},
        "result_count": result_count,
        "ids": ids,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def search_arxiv(query, log_path, email, max_results=50):
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    headers = {"User-Agent": USER_AGENT_TEMPLATE.format(email=email)}
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        log_query(log_path, "arxiv", query, params, 0, [])
        print(f"    arxiv error for '{query}': {e}")
        return []

    parsed = feedparser.parse(resp.text)
    results = []
    for entry in parsed.entries:
        arxiv_id = entry.id.split("/")[-1].split("v")[0]
        results.append({
            "title": entry.title.strip().replace("\n", " "),
            "authors": ", ".join(a.name for a in entry.authors),
            "year": entry.published[:4] if hasattr(entry, "published") else "",
            "venue": "arXiv",
            "abstract": entry.summary.strip().replace("\n", " "),
            "doi": "",
            "arxiv_id": arxiv_id,
            "url": entry.id,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            "source_database": "arxiv",
            "source_query": query,
        })
    log_query(log_path, "arxiv", query, params, len(results),
              [r["arxiv_id"] for r in results])
    return results


def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    positions = []
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def search_openalex(query, log_path, email, max_results=100):
    params = {
        "search": query,
        "per_page": min(max_results, 200),
        "mailto": email,
    }
    try:
        resp = requests.get(OPENALEX_API, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        log_query(log_path, "openalex", query, params, 0, [])
        print(f"    openalex error for '{query}': {e}")
        return []

    data = resp.json()
    results = []
    for work in data.get("results", [])[:max_results]:
        title = work.get("title", "") or ""
        authors_list = [
            a.get("author", {}).get("display_name", "")
            for a in work.get("authorships", [])
        ]
        abstract_inverted = work.get("abstract_inverted_index")
        abstract = reconstruct_abstract(abstract_inverted) if abstract_inverted else ""
        doi = work.get("doi", "") or ""
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]
        oa_url = ""
        oa_loc = work.get("best_oa_location") or {}
        if oa_loc:
            oa_url = oa_loc.get("pdf_url", "") or oa_loc.get("landing_page_url", "")
        results.append({
            "title": title,
            "authors": ", ".join(authors_list),
            "year": str(work.get("publication_year", "")),
            "venue": (work.get("host_venue") or {}).get("display_name", ""),
            "abstract": abstract,
            "doi": doi,
            "arxiv_id": "",
            "url": work.get("id", ""),
            "pdf_url": oa_url,
            "source_database": "openalex",
            "source_query": query,
        })
    log_query(log_path, "openalex", query, params, len(results),
              [r["doi"] or r["url"] for r in results])
    return results


def search_semantic_scholar(query, log_path, email, max_results=100):
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "title,authors,year,venue,abstract,externalIds,openAccessPdf,url",
    }
    headers = {"User-Agent": USER_AGENT_TEMPLATE.format(email=email)}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    try:
        resp = requests.get(SEMANTIC_SCHOLAR_API, params=params,
                            headers=headers, timeout=30)
        if resp.status_code == 429:
            time.sleep(30)
            resp = requests.get(SEMANTIC_SCHOLAR_API, params=params,
                                headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        log_query(log_path, "semantic_scholar", query, params, 0, [])
        print(f"    semantic_scholar error for '{query}': {e}")
        return []

    data = resp.json()
    results = []
    for item in data.get("data", []):
        ext = item.get("externalIds", {}) or {}
        pdf = (item.get("openAccessPdf") or {}).get("url", "")
        results.append({
            "title": item.get("title", "") or "",
            "authors": ", ".join(a.get("name", "") for a in item.get("authors", []) or []),
            "year": str(item.get("year", "") or ""),
            "venue": item.get("venue", "") or "",
            "abstract": item.get("abstract", "") or "",
            "doi": ext.get("DOI", "") or "",
            "arxiv_id": ext.get("ArXiv", "") or "",
            "url": item.get("url", "") or "",
            "pdf_url": pdf,
            "source_database": "semantic_scholar",
            "source_query": query,
        })
    log_query(log_path, "semantic_scholar", query, params, len(results),
              [r["doi"] or r["arxiv_id"] or r["url"] for r in results])
    return results


def normalize_title(t):
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def jaccard(a, b):
    sa = set(a.split())
    sb = set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def deduplicate(rows, jaccard_threshold=0.85):
    by_doi = {}
    no_doi = []
    for r in rows:
        doi = (r.get("doi") or "").lower().strip()
        if doi:
            if doi in by_doi:
                continue
            by_doi[doi] = r
        else:
            no_doi.append(r)

    deduped = list(by_doi.values())
    seen_titles = [normalize_title(r["title"]) for r in deduped]

    for r in no_doi:
        nt = normalize_title(r["title"])
        if not nt:
            continue
        is_dup = any(jaccard(nt, st) >= jaccard_threshold for st in seen_titles)
        if not is_dup:
            deduped.append(r)
            seen_titles.append(nt)

    return deduped


def load_query_bank(protocol_path):
    text = Path(protocol_path).read_text(encoding="utf-8")
    section_re = re.compile(r"## Query bank.*?```(.*?)```", re.DOTALL)
    m = section_re.search(text)
    if not m:
        raise ValueError(f"query bank not found in {protocol_path}")
    queries = [q.strip() for q in m.group(1).strip().splitlines()
               if q.strip() and not q.strip().startswith("#")]
    return queries


def load_email_from_topic(topic_path):
    if not Path(topic_path).exists():
        return None
    text = Path(topic_path).read_text(encoding="utf-8")
    m = re.search(r"contact_email:\s*(\S+)", text)
    if not m:
        return None
    val = m.group(1).strip()
    if val.upper().startswith("REPLACE"):
        return None
    return val


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email",
                        help="contact email for API politeness headers. "
                             "If omitted, read from protocol/topic.md.")
    parser.add_argument("--topic-file", default="protocol/topic.md")
    parser.add_argument("--queries-file", default="protocol/search_queries.md")
    parser.add_argument("--output-csv", default="data/candidates_raw.csv")
    parser.add_argument("--output-log", default="data/search_log.jsonl")
    args = parser.parse_args()

    email = args.email or load_email_from_topic(args.topic_file)
    if not email:
        print("ERROR: no email provided. Either pass --email or set "
              "contact_email in protocol/topic.md.")
        sys.exit(2)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_log).touch()

    queries = load_query_bank(args.queries_file)
    if not queries:
        print(f"ERROR: no queries found in {args.queries_file}")
        sys.exit(2)

    print(f"running {len(queries)} queries with contact email '{email}'")

    all_rows = []
    for q in queries:
        print(f"  query: {q}")
        all_rows.extend(search_arxiv(q, args.output_log, email))
        time.sleep(3)
        all_rows.extend(search_openalex(q, args.output_log, email))
        time.sleep(0.1)
        all_rows.extend(search_semantic_scholar(q, args.output_log, email))
        time.sleep(1.5)

    print(f"total raw results: {len(all_rows)}")
    deduped = deduplicate(all_rows)
    print(f"after deduplication: {len(deduped)}")

    fieldnames = [
        "paper_id", "title", "authors", "year", "venue", "abstract",
        "doi", "arxiv_id", "url", "pdf_url",
        "source_database", "source_query",
    ]
    with open(args.output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in deduped:
            row.setdefault("paper_id", "")
            writer.writerow(row)

    print(f"wrote {len(deduped)} rows to {args.output_csv}")
    print("next: review the CSV, then run stage 2 triage.")


if __name__ == "__main__":
    main()
