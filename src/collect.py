"""Collect SALIC pages into data/raw, one gzipped file per request.

Resumable: a page already on disk is skipped, so an interrupted run is continued by
rerunning the same command. Raw pages are written exactly as received (the response
body, gzipped) plus a small sidecar of request metadata, and are never edited.

Usage:
    python -m src.collect projetos
    python -m src.collect reference
    python -m src.collect proponentes incentivadores
"""
from __future__ import annotations

import gzip
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path

import requests

from src.config import (
    API_BASE,
    AREA_CODES,
    BACKOFF_BASE_S,
    DATA_RAW,
    MAX_RETRIES,
    PAGE_LIMIT,
    REQUEST_PAUSE_S,
    TIMEOUT_S,
)

COLLECTED_ON = date.today().isoformat()
log = logging.getLogger("collect")

# The API answers 301 to plain HTTP when a path carries a trailing slash, so paths
# here never end in one.
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


def _get(path: str, params: dict) -> dict:
    """GET with retry, exponential backoff and respect for Retry-After."""
    url = f"{API_BASE}/{path}"
    for attempt in range(MAX_RETRIES):
        try:
            r = SESSION.get(url, params=params, timeout=TIMEOUT_S, allow_redirects=False)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429 or r.status_code >= 500:
                wait = float(r.headers.get("Retry-After", BACKOFF_BASE_S * (2**attempt)))
                log.warning("%s on %s %s, waiting %.1fs", r.status_code, path, params, wait)
                time.sleep(wait)
                continue
            if r.status_code == 404:
                # The API returns 404 with message_code 11 for an empty result set.
                try:
                    return r.json()
                except ValueError:
                    pass
            r.raise_for_status()
        except (requests.Timeout, requests.ConnectionError) as exc:
            wait = BACKOFF_BASE_S * (2**attempt)
            log.warning("%s on %s %s, waiting %.1fs", type(exc).__name__, path, params, wait)
            time.sleep(wait)
    raise RuntimeError(f"giving up on {path} {params} after {MAX_RETRIES} attempts")


def _write(target: Path, payload: dict, meta: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump({"_meta": meta, "response": payload}, fh, ensure_ascii=False)
    tmp.replace(target)  # atomic, so an interrupted write never leaves a half page


def _page_count(total: int) -> int:
    return (total + PAGE_LIMIT - 1) // PAGE_LIMIT


def collect_projetos() -> None:
    """Sweep the 8 area codes. Each record is fetched once and tagged with its area."""
    for code, name in AREA_CODES.items():
        first = _get("projetos", {"limit": 1, "area": code})
        total = int(first.get("total", 0) or 0)
        pages = _page_count(total)
        log.info("area %s (%s): total=%d, pages=%d", code, name, total, pages)
        for page in range(pages):
            offset = page * PAGE_LIMIT
            target = (
                DATA_RAW / "projetos" / f"collected={COLLECTED_ON}"
                / f"area={code}" / f"offset={offset:07d}.json.gz"
            )
            if target.exists():
                continue
            params = {"limit": PAGE_LIMIT, "offset": offset, "area": code}
            payload = _get("projetos", params)
            _write(target, payload, {
                "endpoint": "projetos", "params": params, "area_code": code,
                "area_nome": name, "collected_on": COLLECTED_ON, "total_at_collection": total,
            })
            if page % 20 == 0:
                log.info("area %s: page %d/%d", code, page + 1, pages)
            time.sleep(REQUEST_PAUSE_S)


def collect_listing(endpoint: str) -> None:
    """Paginate a flat listing endpoint such as proponentes or incentivadores."""
    first = _get(endpoint, {"limit": 1})
    total = int(first.get("total", 0) or 0)
    pages = _page_count(total)
    log.info("%s: total=%d, pages=%d", endpoint, total, pages)
    for page in range(pages):
        offset = page * PAGE_LIMIT
        target = (
            DATA_RAW / endpoint / f"collected={COLLECTED_ON}"
            / f"offset={offset:07d}.json.gz"
        )
        if target.exists():
            continue
        params = {"limit": PAGE_LIMIT, "offset": offset}
        payload = _get(endpoint, params)
        _write(target, payload, {
            "endpoint": endpoint, "params": params,
            "collected_on": COLLECTED_ON, "total_at_collection": total,
        })
        if page % 50 == 0:
            log.info("%s: page %d/%d", endpoint, page + 1, pages)
        time.sleep(REQUEST_PAUSE_S)


def collect_reference() -> None:
    """The small lookup tables: areas and segmentos."""
    for endpoint in ("projetos/areas", "projetos/segmentos"):
        payload = _get(endpoint, {})
        target = DATA_RAW / "reference" / f"collected={COLLECTED_ON}" / (
            endpoint.replace("/", "_") + ".json.gz"
        )
        _write(target, payload, {
            "endpoint": endpoint, "params": {}, "collected_on": COLLECTED_ON,
        })
        log.info("wrote %s", target.name)
        time.sleep(REQUEST_PAUSE_S)


TASKS = {
    "reference": collect_reference,
    "projetos": collect_projetos,
    "proponentes": lambda: collect_listing("proponentes"),
    "incentivadores": lambda: collect_listing("incentivadores"),
}


def main(argv: list[str]) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    names = argv[1:] or ["reference", "projetos"]
    unknown = [n for n in names if n not in TASKS]
    if unknown:
        log.error("unknown task(s): %s. Known: %s", unknown, list(TASKS))
        return 2
    for name in names:
        log.info("=== %s ===", name)
        TASKS[name]()
    log.info("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
