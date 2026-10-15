# Thesis Literature Review Pipeline
#
# Run stages sequentially. Each stage depends on the previous stage's output.
# Stages 2, 4, 5, 6, 7 produce content judgments and run best inside an
# agentic AI tool, a chat LLM, or by hand. Stages 1 and 3 are pure data work
# and run as Python scripts.
#
# All commands work without any AI tool. The "by-hand" targets print the
# checklist for the corresponding stage.

.PHONY: help search manual-triage download deep_read synthesis quality_filter \
        positioning bibliography validate validate-strict clean \
        manual-search manual-triage-howto manual-download manual-deepread \
        manual-synthesis manual-quality manual-positioning \
        docx

help:
	@echo "Thesis Literature Review Pipeline"
	@echo ""
	@echo "Configuration: edit protocol/topic.md and protocol/search_queries.md first."
	@echo ""
	@echo "Stages (run in order):"
	@echo "  make search           Stage 1. Run automated search across three open APIs."
	@echo "  make download         Stage 3. Download PDFs for triaged includes."
	@echo "  make validate         Stage 4 helper. Validate notes/ against the schema."
	@echo "  make bibliography     Optional. Build sources.md and sources.bib from notes/."
	@echo ""
	@echo "Stages 2, 4, 5, 6, 7 require human or AI judgment. Run them through"
	@echo "your chosen agent/LLM tool, or by hand using the agents/NN_*.md files."
	@echo ""
	@echo "By-hand checklists:"
	@echo "  make manual-search        Stage 1 by hand."
	@echo "  make manual-triage-howto  Stage 2 by hand."
	@echo "  make manual-download      Stage 3 by hand."
	@echo "  make manual-deepread      Stage 4 by hand."
	@echo "  make manual-synthesis     Stage 5 by hand."
	@echo "  make manual-quality       Stage 6 by hand."
	@echo "  make manual-positioning   Stage 7 by hand."
	@echo ""
	@echo "Utilities:"
	@echo "  make validate-strict  Run validator and fail on any error."
	@echo "  make clean            Remove all generated artifacts. Templates preserved."

search:
	@echo "Stage 1. Running search."
	python scripts/run_search.py
	python scripts/append_manual_additions.py
	@echo ""
	@echo "next: review data/candidates_raw.csv, then run stage 2 triage."

download:
	@echo "Stage 3. Downloading PDFs."
	@if [ ! -f data/candidates_triaged.csv ]; then \
		echo "ERROR: data/candidates_triaged.csv not found. Run stage 2 first."; \
		exit 1; \
	fi
	python scripts/download_pdfs.py

validate:
	python scripts/validate_notes.py

validate-strict:
	python scripts/validate_notes.py --strict

bibliography:
	python scripts/build_bibliography.py

manual-search:
	@echo "Stage 1 by hand. See agents/01_search.md section 'Run by hand'."

manual-triage-howto:
	@echo "Stage 2 by hand. See agents/02_triage.md section 'Run by hand'."

manual-download:
	@echo "Stage 3 by hand. See agents/03_download.md section 'Run by hand'."

manual-deepread:
	@echo "Stage 4 by hand. See agents/04_deepread.md section 'Run by hand'."
	@echo "The by-hand template is at the bottom of that file."

manual-synthesis:
	@echo "Stage 5 by hand. See agents/05_synthesis.md section 'Run by hand'."

manual-quality:
	@echo "Stage 6 by hand. See agents/06_quality_filter.md section 'Run by hand'."

manual-positioning:
	@echo "Stage 7 by hand. See agents/07_positioning.md section 'Run by hand'."

docx:
	@echo "Convert a Markdown file to a valid .docx."
	@echo "Usage: make docx IN=path/to/file.md [OUT=path/to/file.docx]"
	@if [ -z "$(IN)" ]; then echo "ERROR: set IN=..."; exit 1; fi
	@python scripts/md_to_docx.py "$(IN)" "$(OUT)"

clean:
	rm -f data/candidates_raw.csv data/candidates_triaged.csv
	rm -f data/search_log.jsonl data/triage_summary.md
	rm -f data/download_log.csv data/manual_retrieval_list.md
	rm -f data/deep_read_log.csv
	rm -rf data/pdfs data/triage_batches data/deepread_batches
	rm -f notes/paper_*.md
	rm -f synthesis/gap_matrix.md synthesis/gap_candidates.md
	rm -f synthesis/indicator_assessment.md synthesis/shortlist.md
	rm -f synthesis/positioning_statement.md synthesis/prisma_flow.md
	rm -f synthesis/sources.md synthesis/sources.bib
	mkdir -p data/pdfs
	@echo "Pipeline artifacts cleaned. Templates and protocol files preserved."
