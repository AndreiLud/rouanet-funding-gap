# Reproduces the project end to end. `make all` goes from raw pages to figures.
# Collection is separate from `all` on purpose: it hits a public API for roughly
# 600 requests, so it is not something a reader should trigger by accident.

PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help setup collect interim quality processed model figures app all clean clean-derived

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n", $$1, $$2}'

setup: ## Create the virtualenv and install pinned dependencies
	python3 -m venv .venv
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt

collect: ## Pull every page from the SALIC API into data/raw (resumable, slow)
	$(PY) -u -m src.collect reference projetos

interim: ## Parse raw pages into data/interim/projetos.parquet
	$(PY) -m src.build_interim

quality: ## Run the data quality checklist into reports/quality_report.md
	$(PY) -m src.quality

all: interim quality ## Rebuild everything downstream of data/raw

clean-derived: ## Delete everything the pipeline generates, keeping data/raw
	rm -rf data/interim/* data/processed/* reports/quality_report.md
	find data -name '.gitkeep' -delete -o -true >/dev/null 2>&1 || true
	touch data/interim/.gitkeep data/processed/.gitkeep

clean: clean-derived ## Also delete the raw pages, forcing a full re-collection
	rm -rf data/raw/*
	touch data/raw/.gitkeep
