# Reproduces the project end to end. `make all` goes from raw pages to figures.
# Collection is separate from `all` on purpose: it hits a public API for roughly
# 600 requests, so it is not something a reader should trigger by accident.

PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help setup collect interim quality processed model error figures app-data app all clean clean-derived

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n", $$1, $$2}'

setup: ## Create the virtualenv and install pinned dependencies
	python3 -m venv .venv
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt

collect: ## Pull every page from the SALIC API into data/raw (resumable, slow)
	$(PY) -u -m src.collect reference projetos incentivadores proponentes

interim: ## Parse raw pages into data/interim/projetos.parquet
	$(PY) -m src.build_interim

quality: ## Run the data quality checklist into reports/quality_report.md
	$(PY) -m src.quality

processed: interim ## Apply the cleaning rules and build the DuckDB analytical layer
	$(PY) -m src.build_processed

model: processed ## Baselines and models, scoring the held out cohort once
	$(PY) -m src.model

error: processed ## Where the model fails, into reports/error_analysis.md
	$(PY) -m src.error_analysis

figures: processed ## Render the figures into reports/figures
	$(PY) -m src.figures

app-data: processed ## Build the committed artefact the Streamlit app reads
	$(PY) -m src.build_app_data

app: app-data ## Run the Streamlit app locally
	$(PY) -m streamlit run app/streamlit_app.py

all: interim quality processed model error figures app-data ## Rebuild everything downstream of data/raw

clean-derived: ## Delete everything the pipeline generates, keeping data/raw
	rm -rf data/interim/* data/processed/* reports/*.md reports/*.csv \
	       reports/*.json reports/figures/*.png app/data/*
	find data -name '.gitkeep' -delete -o -true >/dev/null 2>&1 || true
	touch data/interim/.gitkeep data/processed/.gitkeep

clean: clean-derived ## Also delete the raw pages, forcing a full re-collection
	rm -rf data/raw/*
	touch data/raw/.gitkeep
