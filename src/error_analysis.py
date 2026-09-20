"""Where the model fails, and why.

The headline failure is not a subgroup, it is a shift over time. The model ranks the
held out cohort adequately and prices it badly: it predicts a mean probability far above
the rate that actually happened. The cause is in the proponent history features, whose
meaning drifts as the observation window lengthens, and this module measures that rather
than asserting it.

Importance here is association, not cause. A feature that moves with the outcome may be
a proxy for something the data does not contain, and for this question the biggest
missing thing is whether the producer already knows a sponsor.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.config import REPORTS, SEED
from src.features import CATEGORICAL, NUMERIC, TARGET, build
from src.model import SegmentUFRate, metrics, preprocessor

log = logging.getLogger("error_analysis")


def calibration_table(y, p, bins: int = 10) -> pd.DataFrame:
    d = pd.DataFrame({"p": np.asarray(p), "y": np.asarray(y)})
    d["bin"] = pd.qcut(d["p"], bins, duplicates="drop", labels=False)
    return d.groupby("bin").agg(n=("y", "size"), mean_pred=("p", "mean"),
                                actual=("y", "mean")).round(4)


def by_group(df: pd.DataFrame, p: np.ndarray, y: np.ndarray, col: str,
             min_n: int = 40) -> pd.DataFrame:
    d = df[[col]].copy()
    d["p"], d["y"] = p, y
    g = d.groupby(col).agg(n=("y", "size"), actual=("y", "mean"), predicted=("p", "mean"))
    g = g[g["n"] >= min_n]
    g["gap"] = (g["predicted"] - g["actual"]).round(4)
    g["brier"] = d.groupby(col).apply(
        lambda x: float(np.mean((x["p"] - x["y"]) ** 2)), include_groups=False)
    return g.round(4).sort_values("gap", ascending=False)


def value_band(v: pd.Series) -> pd.Series:
    return pd.cut(v, [0, 1e5, 5e5, 1e6, 5e6, np.inf],
                  labels=["under 100k", "100k to 500k", "500k to 1M", "1M to 5M",
                          "5M and above"])


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = build(pd.read_parquet("data/processed/projetos.parquet"))
    s = df[df["in_model_sample"]].reset_index(drop=True)
    tr, te = s[s["split"] == "train"], s[s["split"] == "test"]
    cols = NUMERIC + CATEGORICAL

    model = Pipeline([("prep", preprocessor()),
                      ("clf", LogisticRegression(max_iter=2000, random_state=SEED))])
    model.fit(tr[cols], tr[TARGET].astype(int))
    heur = SegmentUFRate().fit(tr[cols], tr[TARGET].astype(int))

    yte = te[TARGET].astype(int).to_numpy()
    p_model = model.predict_proba(te[cols])[:, 1]
    p_heur = heur.predict_proba(te[cols])[:, 1]

    out = ["# Error analysis", "",
           f"Held out cohort 2022, n = {len(te):,}, actual rate "
           f"{yte.mean():.3f}.", "",
           "## The failure is the level, not the ranking", "",
           f"- model mean predicted probability: {p_model.mean():.3f}",
           f"- heuristic mean predicted probability: {p_heur.mean():.3f}",
           f"- what actually happened: {yte.mean():.3f}", "",
           "The model prices the cohort far above what happened while still ordering it "
           "sensibly, which is why its PR-AUC beats the heuristic and its Brier score "
           "loses to it.", "",
           "## Calibration on the held out cohort", "",
           "Model:", "", calibration_table(yte, p_model).to_markdown(), "",
           "Heuristic:", "", calibration_table(yte, p_heur).to_markdown(), ""]

    # The drift that causes it
    drift = []
    for c in NUMERIC:
        drift.append({"feature": c,
                      "train_median": round(float(tr[c].median()), 2),
                      "test_median": round(float(te[c].median()), 2),
                      "train_missing": round(float(tr[c].isna().mean()), 3),
                      "test_missing": round(float(te[c].isna().mean()), 3)})
    out += ["## Feature drift between train and the held out cohort", "",
            pd.DataFrame(drift).to_markdown(index=False), "",
            "The proponent history features are the ones that matter here. Their "
            "missing rate falls as the observation window lengthens, and the observed "
            "prior success rate drifts upwards because proponents who appear repeatedly "
            "are disproportionately the ones who succeeded. The feature means something "
            "different in 2022 than it meant in 2020, which is a property of the window "
            "and not of the projects.", ""]

    # Subgroup errors
    te2 = te.copy()
    te2["faixa_valor"] = value_band(te2["valor_solicitado"])
    for col, label in [("area", "area"), ("UF", "state"), ("faixa_valor", "value band")]:
        out += [f"## Error by {label}", "",
                by_group(te2, p_model, yte, col).to_markdown(), ""]

    # Permutation importance, stated as association
    r = permutation_importance(model, te[cols], yte, n_repeats=5, random_state=SEED,
                               scoring="average_precision")
    imp = pd.Series(r.importances_mean, index=cols).sort_values(ascending=False)
    out += ["## Permutation importance on the held out cohort", "",
            "Drop in PR-AUC when the feature is shuffled. This is association, not "
            "cause: none of these is a lever a producer can pull.", "",
            imp.round(4).to_frame("drop_in_pr_auc").to_markdown(), ""]

    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / "error_analysis.md"
    path.write_text("\n".join(out), encoding="utf-8")
    log.info("wrote %s", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
