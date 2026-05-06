# Stage 3. Download

## Role

Fetch PDFs for every paper labelled `include` or `maybe` in the triage output. Record successes and failures. Do not read the PDFs.

## Inputs

```
data/candidates_triaged.csv
protocol/topic.md   (for the contact email)
```

## Outputs

```
data/pdfs/paper_NNN.pdf  (one per successful download)
data/download_log.csv
data/manual_retrieval_list.md
```

## Procedure (agentic AI mode)

Run `python scripts/download_pdfs.py --email "$contact_email"` from the repository root. The script handles the full resolution chain (direct PDF URL, arXiv direct, Unpaywall lookup), validates each downloaded file by magic bytes, and writes the log and manual retrieval list.

After the script completes, report total successful downloads and total manual retrieval entries to the user. A success rate below 70 percent indicates either heavy paywalling of the active topic or an issue with the resolution chain. Report this to the user.

If the script needs adjustment for a specific publisher (some open-access publishers require special headers or use unusual URL patterns), edit the resolution chain in the script. Always rate-limit at one request per second per host. Always honor 429 and 503 responses with exponential backoff. Do not bypass paywalls.

## Procedure (single-shot LLM mode)

The single-shot LLM cannot fetch PDFs. Run `python scripts/download_pdfs.py` yourself outside the chat. The LLM has no role at stage three. Skip to stage four.

## Procedure (by hand)

Open `data/candidates_triaged.csv` in a spreadsheet. Filter to rows where `triage_label` is `include` or `maybe`. For each row, in this order:

1. If the row has `pdf_url` filled in, click it. If the file downloads as a PDF, save it to `data/pdfs/paper_NNN.pdf` using the paper_id from the CSV.
2. If the row has `arxiv_id` but no `pdf_url`, open `https://arxiv.org/pdf/<arxiv_id>.pdf` in the browser.
3. If the row has only a DOI, open `https://api.unpaywall.org/v2/<doi>?email=YOUR_EMAIL` in the browser. The JSON response has a `best_oa_location.url_for_pdf` field. Open that URL.
4. If none of the above resolves a PDF, search for the title in Google Scholar. Click any green "[PDF]" link. If only paywalled versions exist, list the paper for manual retrieval.

For every download attempt, log to `data/download_log.csv`:

```
paper_id, attempted_url, status, file_size_bytes, error_message
```

`status` is `success`, `failed`, or `already_present`.

For every paper that could not be downloaded, append an entry to `data/manual_retrieval_list.md`:

```markdown
## paper_NNN

Title. ...
Authors. ...
Year. ...
Venue. ...
DOI. ...
URL. ...
Suggested retrieval. Try institutional VPN, ResearchGate, or direct author email.
```

## Verification

Every downloaded file must be a valid PDF. Open one or two to spot-check that the file is the paper claimed by the row. Files that turn out to be HTML "preview" pages are not valid PDFs. Delete them and add the paper to the manual retrieval list.

The script verifies magic bytes (`%PDF-`) and file size (between 100 KB and 50 MB). By hand, eyeball the file size in the file manager. A 5 KB "PDF" is not a PDF.

## Politeness rules

Rate limit at one request per second per host. Set User-Agent to `LitReview/1.0 (mailto:YOUR_EMAIL)`. Honor 429 and 503 responses with backoff. Do not use Sci-Hub. Do not bypass paywalls. The manual retrieval list exists for papers that cannot be obtained through legitimate open-access channels.

## Anti-context-fatigue rule

You do not open the PDFs at this stage. You do not summarize them. You do not classify them. The only task is to fetch the bytes and verify they are valid PDF files.

## Stop conditions

Stage three stops when every paper in the include and maybe lists has either a downloaded PDF in `data/pdfs/` or an entry in `data/manual_retrieval_list.md`. Report total successful downloads and total manual retrieval entries to the user.

A successful download rate below 70 percent indicates either heavy paywalling of the active topic or an issue with the resolution chain. Investigate before proceeding to stage four.
