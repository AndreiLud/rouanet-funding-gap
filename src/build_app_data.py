"""Build the small committed artefacts the Streamlit app reads.

The app runs on Streamlit Community Cloud from the repository alone, and data/ is
untracked, so anything the app needs has to be committed. Two things are committed:

- `app/data/sample.csv`: the analysable projects reduced to the columns the app
  aggregates over. It carries no identifier of any kind, not even a hash, so there is
  nothing to re-identify: category, state, requested amount, cohort and outcome.
- `app/data/model.joblib` plus `app/data/model_meta.json`: the fitted pipeline and the
  medians used to fill the features a producer cannot supply at decision time.

Shipping the rows rather than a precomputed grid of rates lets the app report an honest
n and confidence interval for whatever combination the producer picks, including the
combinations that turn out to be too thin to say anything about.
"""
from __future__ import annotations

import json
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.config import DATA_PROCESSED, ROOT, SEED
from src.features import CATEGORICAL, NUMERIC, TARGET, build
from src.model import preprocessor

log = logging.getLogger("build_app_data")

APP_DATA = ROOT / "app" / "data"
# What a producer can actually answer when sizing a budget.
USER_INPUTS = ["area", "segmento", "UF", "valor_solicitado", "prior_projetos",
               "prior_taxa_ge50"]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = build(pd.read_parquet(DATA_PROCESSED / "projetos.parquet"))
    s = df[df["in_model_sample"]].reset_index(drop=True)

    APP_DATA.mkdir(parents=True, exist_ok=True)
    sample = s[["area", "segmento", "UF", "valor_solicitado", "ano_projeto",
                "target_ge50", "share_raised_capped"]].copy()
    sample.to_csv(APP_DATA / "sample.csv", index=False)

    cols = NUMERIC + CATEGORICAL
    model = Pipeline([("prep", preprocessor()),
                      ("clf", LogisticRegression(max_iter=2000, random_state=SEED))])
    model.fit(s[cols], s[TARGET].astype(int))
    joblib.dump(model, APP_DATA / "model.joblib", compress=3)

    # The app asks for six things. Everything else the model wants is filled with the
    # training median, and the app says so rather than implying the producer supplied it.
    fill = {c: (None if c in USER_INPUTS else
                (float(s[c].median()) if c in NUMERIC else str(s[c].mode().iloc[0])))
            for c in cols}
    meta = {
        "filled_with_median": sorted(c for c in cols if c not in USER_INPUTS),
        "user_supplied": sorted(c for c in cols if c in USER_INPUTS),
        "fill_values": {k: v for k, v in fill.items() if v is not None},
        "areas": sorted(s["area"].dropna().unique().tolist()),
        "ufs": sorted(s["UF"].dropna().unique().tolist()),
        "segmentos_by_area": {a: sorted(g["segmento"].dropna().unique().tolist())
                              for a, g in s.groupby("area")},
        "n_total": int(len(s)),
        "base_rate": float(s[TARGET].mean()),
        "cohorts": [int(x) for x in sorted(s["ano_projeto"].unique())],
        "collected_on": "2026-09-20",
        # Measured on the held out cohort in reports/error_analysis.md.
        "test_mean_predicted": 0.767,
        "test_actual_rate": 0.437,
    }
    (APP_DATA / "model_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                              encoding="utf-8")
    for p in sorted(APP_DATA.glob("*")):
        log.info("wrote %s (%.0f KB)", p.name, p.stat().st_size / 1024)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
