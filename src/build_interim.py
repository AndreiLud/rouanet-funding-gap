"""Parse raw SALIC pages into one flat table in data/interim.

Three decisions worth stating, because they are not reversible downstream without
going back to the raw pages:

1. LGPD. `cgccpf` and `proponente` never leave data/raw. The proponent is carried
   forward only as a salted hash, which is enough to group a proponent's projects and
   to count concentration, and is not enough to name anybody. Some proponents are
   individuals trading under a CNPJ whose registered name contains their own name, so
   dropping the name is safer than trying to classify who is a natural person.
2. The salt is generated once into a gitignored file. A random salt per machine means
   the hashes are not comparable across checkouts, which is deliberate: every aggregate
   this project reports is identical either way, and a fixed committed salt would make
   the hashes reversible by anyone with the repository.
3. Free text is reduced to character counts. The raw pages keep every character, so
   nothing is lost and text features can be re-derived, but carrying roughly 1.6 GB of
   project prose into every downstream step buys nothing the counts do not.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import logging
import secrets
from pathlib import Path

import pandas as pd

from src.config import DATA_INTERIM, DATA_RAW, ROOT

log = logging.getLogger("build_interim")

SALT_FILE = ROOT / "proponente.salt"

MONEY_FIELDS = [
    "valor_solicitado", "valor_aprovado", "valor_projeto",
    "valor_captado", "valor_proposta", "outras_fontes",
]
TEXT_FIELDS = [
    "objetivos", "justificativa", "resumo", "sinopse", "etapa", "ficha_tecnica",
    "acessibilidade", "democratizacao", "impacto_ambiental",
    "especificacao_tecnica", "estrategia_execucao", "providencia",
]
# The API spells these two this way. Renamed here, once, at the boundary.
RENAME = {"enquadradmento": "enquadramento", "mecanisnmo": "mecanismo"}


def _salt() -> str:
    if not SALT_FILE.exists():
        SALT_FILE.write_text(secrets.token_hex(32), encoding="utf-8")
        log.info("generated a new proponent salt at %s (gitignored)", SALT_FILE.name)
    return SALT_FILE.read_text(encoding="utf-8").strip()


def _hash(value: str, salt: str) -> str | None:
    v = (value or "").strip()
    if not v:
        return None
    return hashlib.sha256((salt + v).encode("utf-8")).hexdigest()[:16]


def _money(value) -> float | None:
    """Money arrives as int, float, or a string like '.0000' or '1234,56'."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        return None


def _year(two_digit) -> int | None:
    """`ano_projeto` is two digits. Coverage starts in 2019, so every value is 20xx."""
    s = str(two_digit or "").strip()
    if not s.isdigit():
        return None
    return 2000 + int(s)


def iter_raw_pages(collected_on: str | None = None):
    root = DATA_RAW / "projetos"
    pattern = f"collected={collected_on}" if collected_on else "collected=*"
    for path in sorted(root.glob(f"{pattern}/area=*/offset=*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            blob = json.load(fh)
        yield path, blob["_meta"], blob["response"]


def build(collected_on: str | None = None) -> pd.DataFrame:
    salt = _salt()
    rows: list[dict] = []
    pages = 0
    for path, meta, response in iter_raw_pages(collected_on):
        pages += 1
        for rec in response.get("_embedded", {}).get("projetos", []):
            row = {
                "PRONAC": str(rec.get("PRONAC", "")).strip(),
                "area_codigo": meta["area_code"],
                "area": meta["area_nome"],
                "segmento": rec.get("segmento"),
                "tipicidade": rec.get("tipicidade"),
                "tipologia": rec.get("tipologia"),
                "UF": rec.get("UF"),
                "municipio": rec.get("municipio"),
                "situacao": rec.get("situacao"),
                "ano_projeto": _year(rec.get("ano_projeto")),
                "data_inicio": rec.get("data_inicio"),
                "data_termino": rec.get("data_termino"),
                "proponente_hash": _hash(rec.get("cgccpf"), salt),
                # A CPF has 11 digits, a CNPJ 14. Used only to flag the row, never to name.
                "proponente_pessoa_fisica": len(
                    "".join(ch for ch in str(rec.get("cgccpf") or "") if ch.isdigit())
                ) == 11,
                "n_municipios": len(rec.get("local_realizacao") or []),
                "_source_page": path.name,
                "_source_area": meta["area_code"],
                "_collected_on": meta["collected_on"],
            }
            for field in MONEY_FIELDS:
                row[field] = _money(rec.get(field))
            for field, target in RENAME.items():
                row[target] = rec.get(field)
            for field in TEXT_FIELDS:
                row[f"len_{field}"] = len(str(rec.get(field) or ""))
            rows.append(row)
    df = pd.DataFrame(rows)
    log.info("parsed %d pages into %d rows", pages, len(df))
    return df


def build_incentivadores(collected_on: str | None = None) -> pd.DataFrame:
    """Sponsors. `total_doado` is a lifetime total with no time dimension, so this
    supports a cross section of concentration and not a per year series. Sponsors are
    carried as a salted hash for the same reason proponents are: some are individuals.
    """
    salt = _salt()
    root = DATA_RAW / "incentivadores"
    pattern = f"collected={collected_on}" if collected_on else "collected=*"
    rows = []
    for path in sorted(root.glob(f"{pattern}/offset=*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            blob = json.load(fh)
        for rec in blob["response"].get("_embedded", {}).get("incentivadores", []):
            rows.append({
                "incentivador_hash": _hash(rec.get("cgccpf"), salt),
                "tipo_pessoa": rec.get("tipo_pessoa"),
                "UF": rec.get("UF"),
                "total_doado": _money(rec.get("total_doado")),
            })
    df = pd.DataFrame(rows)
    log.info("parsed %d sponsors", len(df))
    return df


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = build()
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    out = DATA_INTERIM / "projetos.parquet"
    df.to_parquet(out, index=False)
    log.info("wrote %s (%d rows, %d cols)", out, len(df), df.shape[1])

    inc = build_incentivadores()
    if len(inc):
        out_inc = DATA_INTERIM / "incentivadores.parquet"
        inc.to_parquet(out_inc, index=False)
        log.info("wrote %s (%d rows)", out_inc, len(inc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
