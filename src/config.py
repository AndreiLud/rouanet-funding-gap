"""Single source of truth for paths, seeds and API constants.

Field names from the SALIC API are kept exactly as the API spells them, including
the typos `enquadradmento` and `mecanisnmo`, so a processed row can always be traced
back to a raw page.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
DUCKDB_PATH = DATA_PROCESSED / "rouanet.duckdb"

SEED = 20260920

# API contract, verified live on 2026-09-20. See docs/project_brief.md section 3.
API_BASE = "https://api.salic.cultura.gov.br/api/v1"
PAGE_LIMIT = 100  # the API caps limit at 100

# `area` is not returned in the project payload, so the sweep tags each record with
# the code it was requested under. These 8 codes partition the project universe.
AREA_CODES = {
    "1": "Artes Cenicas",
    "2": "Audiovisual",
    "3": "Musica",
    "4": "Artes Visuais",
    "5": "Patrimonio Cultural",
    "6": "Humanidades",
    "7": "Artes Integradas",
    "9": "Museus e Memoria",
}

# Pacing. Observed on 2026-09-20: a sustained sweep at 0.35s between requests gets
# rate limited after a few hundred pages, and the API then answers with a Retry-After
# that the collector honours, which stretches a page out to minutes. A slower steady
# pace finishes sooner than a fast one that trips the limiter.
REQUEST_PAUSE_S = 1.0
MAX_RETRIES = 6
BACKOFF_BASE_S = 2.0
TIMEOUT_S = 180
