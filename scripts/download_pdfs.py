#!/usr/bin/env python3
"""
PDF download helper. Stage 3.

Reads data/candidates_triaged.csv, filters to papers labelled include or
maybe, and attempts to download each PDF using a resolution chain.

Resolution chain per paper:
  1. The pdf_url column from search results.
  2. https://arxiv.org/pdf/<arxiv_id>.pdf if arxiv_id is set.
  3. The Unpaywall API for the DOI.

Writes data/pdfs/paper_NNN.pdf for successes and
data/manual_retrieval_list.md for failures.

Standalone. No AI required.

Usage:
    python scripts/download_pdfs.py
    python scripts/download_pdfs.py --email [email protected]
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Required: requests. Install with: pip install requests")
    sys.exit(2)


PDF_MAGIC = b"%PDF-"
MIN_PDF_SIZE = 100 * 1024
MAX_PDF_SIZE = 50 * 1024 * 1024

USER_AGENT_TEMPLATE = "LitReview/1.0 (mailto:{email})"


def is_valid_pdf(content: bytes) -> tuple[bool, str]:
    if len(content) < MIN_PDF_SIZE:
        return False, f"too small ({len(content)} bytes)"
    if len(content) > MAX_PDF_SIZE:
        return False, f"too large ({len(content)} bytes)"
    if not content.startswith(PDF_MAGIC):
        return False, "not a PDF (wrong magic bytes)"
    return True, "ok"


def try_download(url: str, headers: dict) -> tuple[bytes | None, str]:
    if not url:
        return None, "no url"
    try:
        resp = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        if resp.status_code in (429, 503):
            time.sleep(30)
            resp = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            return None, f"http {resp.status_code}"
        return resp.content, "ok"
    except requests.RequestException as e:
        return None, f"request error: {e}"


def query_unpaywall(doi: str, email: str) -> str:
    if not doi:
        return ""
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return ""
        data = resp.json()
        loc = data.get("best_oa_location") or {}
        return loc.get("url_for_pdf", "") or ""
    except (requests.RequestException, ValueError):
        return ""


def resolve_pdf_url(row: dict, email: str) -> list[tuple[str, str]]:
    candidates = []
    if row.get("pdf_url"):
        candidates.append((row["pdf_url"], "primary pdf_url"))
    if row.get("arxiv_id"):
        arxiv_id = row["arxiv_id"].strip()
        candidates.append((f"https://arxiv.org/pdf/{arxiv_id}.pdf", "arxiv direct"))
    if row.get("doi"):
        oa_url = query_unpaywall(row["doi"], email)
        if oa_url:
            candidates.append((oa_url, "unpaywall"))
    return candidates


def download_one(row: dict, pdf_dir: Path, email: str) -> dict:
    paper_id = row["paper_id"]
    out_path = pdf_dir / f"paper_{paper_id}.pdf"

    if out_path.exists() and out_path.stat().st_size >= MIN_PDF_SIZE:
        return {
            "paper_id": paper_id,
            "attempted_url": str(out_path),
            "status": "already_present",
            "file_size_bytes": out_path.stat().st_size,
            "error_message": "",
        }

    candidates = resolve_pdf_url(row, email)
    headers = {"User-Agent": USER_AGENT_TEMPLATE.format(email=email)}

    for url, source in candidates:
        content, _ = try_download(url, headers)
        if content is None:
            continue
        valid, _ = is_valid_pdf(content)
        if valid:
            out_path.write_bytes(content)
            return {
                "paper_id": paper_id,
                "attempted_url": url,
                "status": "success",
                "file_size_bytes": len(content),
                "error_message": "",
            }
        time.sleep(1)

    return {
        "paper_id": paper_id,
        "attempted_url": ", ".join(c[0] for c in candidates) or "(none resolved)",
        "status": "failed",
        "file_size_bytes": 0,
        "error_message": "no candidate yielded a valid PDF",
    }


def load_email_from_topic(topic_path: str) -> str | None:
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
                        help="contact email. If omitted, read from "
                             "protocol/topic.md.")
    parser.add_argument("--topic-file", default="protocol/topic.md")
    parser.add_argument("--triaged-csv", default="data/candidates_triaged.csv")
    parser.add_argument("--pdf-dir", default="data/pdfs")
    parser.add_argument("--log-csv", default="data/download_log.csv")
    parser.add_argument("--manual-list", default="data/manual_retrieval_list.md")
    args = parser.parse_args()

    email = args.email or load_email_from_topic(args.topic_file)
    if not email:
        print("ERROR: no email provided. Either pass --email or set "
              "contact_email in protocol/topic.md.")
        sys.exit(2)

    pdf_dir = Path(args.pdf_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    with open(args.triaged_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("triage_label") in {"include", "maybe"}]

    print(f"attempting download for {len(rows)} papers")

    log_rows = []
    failures = []
    for i, row in enumerate(rows, 1):
        print(f"  [{i}/{len(rows)}] paper_{row['paper_id']}")
        result = download_one(row, pdf_dir, email)
        log_rows.append(result)
        if result["status"] == "failed":
            failures.append(row)
        time.sleep(1)

    fieldnames = ["paper_id", "attempted_url", "status",
                  "file_size_bytes", "error_message"]
    with open(args.log_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    if failures:
        with open(args.manual_list, "w", encoding="utf-8") as f:
            f.write("# Manual Retrieval List\n\n")
            f.write("Papers that could not be downloaded automatically. ")
            f.write("Retrieve through institutional access or direct author contact.\n\n")
            for row in failures:
                f.write(f"## paper_{row['paper_id']}\n\n")
                f.write(f"Title. {row.get('title', '')}\n\n")
                f.write(f"Authors. {row.get('authors', '')}\n\n")
                f.write(f"Year. {row.get('year', '')}\n\n")
                f.write(f"Venue. {row.get('venue', '')}\n\n")
                f.write(f"DOI. {row.get('doi', '')}\n\n")
                f.write(f"URL. {row.get('url', '')}\n\n")
                f.write("Suggested retrieval. Try institutional VPN, ResearchGate, or direct author email.\n\n")

    success_count = sum(1 for r in log_rows
                        if r["status"] in {"success", "already_present"})
    print(f"\nresult: {success_count}/{len(log_rows)} succeeded, "
          f"{len(failures)} require manual retrieval")
    print("next: review download_log.csv, retrieve manual list if any, "
          "then run stage 4 deep read.")


if __name__ == "__main__":
    main()
