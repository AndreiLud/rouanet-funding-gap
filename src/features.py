"""Build the model matrix using only what is knowable at approval.

The exclusion list lives in docs/data_dictionary.md. The rule that needs care in code,
rather than in prose, is the proponent history: a project may only see projects from
strictly earlier approval cohorts, so a 2021 project sees 2019 and 2020 and nothing
else. Computing it with a groupby over the whole table would leak the future into the
past, which is the most common way this kind of feature goes wrong.

Known limitation: the API starts at approval year 2019, so a proponent who was active
before then looks like a newcomer. "First project we can see" is not "first project".
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger("features")

# `valor_aprovado` and anything derived from it are absent on purpose. The approved
# amount is revised after the outcome, so it leaks: a ratio of approved to requested
# carried the entire first version of this model (permutation importance 0.271 against
# 0.012 for the next feature) and was encoding whether the project had already raised
# money. `valor_projeto` is out for the same reason, being approved plus other sources.
NUMERIC = [
    "valor_solicitado_log", "outras_fontes_log",
    "n_municipios", "duracao_dias",
    "len_objetivos", "len_justificativa", "len_resumo", "len_ficha_tecnica",
    "len_etapa", "len_democratizacao", "len_especificacao_tecnica",
    "prior_projetos", "prior_taxa_ge50", "prior_captado_log",
]
CATEGORICAL = [
    "area", "segmento", "tipicidade", "tipologia", "UF", "mecanismo", "enquadramento",
]
TARGET = "target_ge50"


def _log1p(s: pd.Series) -> pd.Series:
    return np.log1p(s.clip(lower=0))


def proponent_history(df: pd.DataFrame) -> pd.DataFrame:
    """Expanding history over approval cohorts, strictly backward looking.

    For each cohort year, the history is built from the cohorts before it only. A
    proponent seen for the first time gets NaN, not zero: "no track record" and "a
    track record of nothing" are different states and the model should be able to
    tell them apart.
    """
    hist = []
    closed = df[df["in_model_sample"]]
    for year in sorted(df["ano_projeto"].dropna().unique()):
        past = closed[closed["ano_projeto"] < year]
        if past.empty:
            agg = pd.DataFrame(columns=["prior_projetos", "prior_ge50", "prior_captado"])
        else:
            agg = past.groupby("proponente_hash").agg(
                prior_projetos=("PRONAC", "size"),
                prior_ge50=("target_ge50", "sum"),
                prior_captado=("valor_captado", "sum"),
            )
        cur = df[df["ano_projeto"] == year][["PRONAC", "proponente_hash"]].copy()
        cur = cur.merge(agg, how="left", left_on="proponente_hash", right_index=True)
        hist.append(cur)
    out = pd.concat(hist, ignore_index=True)
    # The earliest cohort has no prior data at all, so those columns arrive as object
    # dtype from an empty frame. Coerce before any arithmetic touches them.
    for col in ("prior_projetos", "prior_ge50", "prior_captado"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["prior_taxa_ge50"] = out["prior_ge50"] / out["prior_projetos"]
    return out[["PRONAC", "prior_projetos", "prior_taxa_ge50", "prior_captado"]]


def build(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["valor_solicitado_log"] = _log1p(out["valor_solicitado"])
    out["outras_fontes_log"] = _log1p(out["outras_fontes"])

    hist = proponent_history(out)
    out = out.merge(hist, on="PRONAC", how="left")
    out["prior_captado_log"] = _log1p(out["prior_captado"])
    out.loc[out["prior_projetos"].isna(), "prior_captado_log"] = np.nan

    missing = [c for c in NUMERIC + CATEGORICAL if c not in out.columns]
    if missing:
        raise KeyError(f"features missing from the table: {missing}")
    return out


def xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[NUMERIC + CATEGORICAL], df[TARGET].astype(int)
