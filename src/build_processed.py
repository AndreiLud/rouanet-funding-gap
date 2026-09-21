"""Apply the cleaning decisions and build the analytical layer.

Every rule here is written down in docs/cleaning_log.md with the count it was taken
against. The table keeps all 61,337 projects and carries flags, rather than filtering
early, so the exploratory analysis can describe the cohorts that modelling excludes and
a reader can see exactly what was dropped and why.
"""
from __future__ import annotations

import logging

import duckdb
import numpy as np
import pandas as pd

from src.cohorts import classify, window_state
from src.config import DATA_INTERIM, DATA_PROCESSED, DUCKDB_PATH

log = logging.getLogger("build_processed")

MODEL_COHORTS = (2019, 2022)  # essentially fully closed: 0.1% to 1.1% still open
THRESHOLDS = {"gt0": 0.0, "ge20": 0.20, "ge50": 0.50, "ge100": 1.00}


def build(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Negative money is not a real quantity. Null rather than clip: a clipped zero
    # would read as "approved for nothing" and enter the counts.
    for col in ("valor_aprovado", "valor_projeto", "valor_solicitado",
                "valor_captado", "valor_proposta", "outras_fontes"):
        out.loc[out[col] < 0, col] = np.nan

    out["state"] = out["situacao"].map(classify)
    out["window_state"] = out["situacao"].map(window_state)
    out["withdrawn"] = out["state"] == "withdrawn"

    # The denominator is `valor_solicitado`, the amount requested at submission, NOT
    # `valor_aprovado`. The approved amount is revised downwards during the accounting
    # phase to match what was actually raised, which only happens to projects that
    # raised something: it is revised for 31.7% of projects that raised money and 1.3%
    # of those that did not, and the revisions sit in the prestacao de contas statuses.
    # A share of a revised approved amount is therefore partly a function of its own
    # numerator. See docs/data_dictionary.md.
    #
    # Requesting is also the decision the producer actually controls, so the ratio to
    # the requested amount is the quantity the question is about.
    out["has_approved_amount"] = out["valor_aprovado"] > 0   # the approval gate
    out["has_requested_amount"] = out["valor_solicitado"] > 0
    out["share_raised"] = np.where(
        out["has_requested_amount"], out["valor_captado"] / out["valor_solicitado"], np.nan
    )
    # Kept only to report the sensitivity of the headline to this choice.
    out["share_raised_vs_aprovado"] = np.where(
        out["has_approved_amount"], out["valor_captado"] / out["valor_aprovado"], np.nan
    )
    # Capped copy for continuous reporting only. A small share sit above 1 and the
    # maximum is not a real outcome. The binary targets use the uncapped share, where
    # anything above 1 clears every threshold anyway.
    out["share_raised_capped"] = out["share_raised"].clip(upper=1.0)

    for name, cut in THRESHOLDS.items():
        out[f"target_{name}"] = np.where(
            out["share_raised"].isna(), np.nan,
            (out["share_raised"] > cut if cut == 0 else out["share_raised"] >= cut),
        )

    lo, hi = MODEL_COHORTS
    out["in_model_sample"] = (
        (out["window_state"] == "closed")
        & out["has_approved_amount"]      # the project was approved at all
        & out["has_requested_amount"]     # the target's denominator exists
        & out["ano_projeto"].between(lo, hi)
    )
    # Train on the older cohorts, hold the most recent closed cohort back. The test set
    # is scored once, at the end.
    out["split"] = np.where(
        ~out["in_model_sample"], "excluded",
        np.where(out["ano_projeto"] < hi, "train", "test"),
    )

    out["duracao_dias"] = (
        pd.to_datetime(out["data_termino"], errors="coerce")
        - pd.to_datetime(out["data_inicio"], errors="coerce")
    ).dt.days
    out.loc[out["duracao_dias"] < 0, "duracao_dias"] = np.nan
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = pd.read_parquet(DATA_INTERIM / "projetos.parquet")
    out = build(df)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    path = DATA_PROCESSED / "projetos.parquet"
    out.to_parquet(path, index=False)

    DUCKDB_PATH.unlink(missing_ok=True)
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE TABLE projetos AS SELECT * FROM read_parquet(?)", [str(path)])
    con.execute("""
        CREATE VIEW analysable AS
        SELECT * FROM projetos WHERE in_model_sample
    """)
    inc_path = DATA_INTERIM / "incentivadores.parquet"
    if inc_path.exists():
        con.execute("CREATE TABLE incentivadores AS SELECT * FROM read_parquet(?)",
                    [str(inc_path)])
    n = con.execute("SELECT count(*) FROM analysable").fetchone()[0]
    con.close()

    log.info("wrote %s (%d rows)", path, len(out))
    log.info("wrote %s (analysable rows: %d)", DUCKDB_PATH, n)
    for split, grp in out.groupby("split"):
        log.info("  split=%-8s %6d", split, len(grp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
