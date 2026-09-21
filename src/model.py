"""Baselines, models and a single scoring of the held out cohort.

Design decisions that matter more than the algorithms:

- The split is temporal by approval cohort. Train is 2019 to 2021, test is 2022. Tuning
  uses time ordered folds inside train only (fit on 2019, validate on 2020; fit on 2019
  and 2020, validate on 2021), so nothing from 2022 informs any choice.
- The heuristic baseline is the rule a producer could apply unaided: the historical rate
  for that segment in that state. It is implemented as an estimator so that it is refit
  inside every fold rather than computed once over all the data, which would let the
  validation years leak into the rule they are scoring.
- Calibration is not an afterthought. The app shows a probability, so being right at
  each probability level matters more than ranking, and the calibrated model is the one
  the app will use.
"""
from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import REPORTS, SEED
from src.features import CATEGORICAL, NUMERIC, TARGET, build

log = logging.getLogger("model")


class SegmentUFRate(BaseEstimator, ClassifierMixin):
    """The rule a producer could apply without a model: the historical rate for this
    segment in this state, backing off to segment, then state, then the overall rate
    when a cell is too thin to trust."""

    def __init__(self, min_cell: int = 30):
        self.min_cell = min_cell

    def fit(self, X, y):
        d = X[["segmento", "UF"]].copy()
        d["y"] = np.asarray(y)
        self.classes_ = np.array([0, 1])
        self.global_ = d["y"].mean()
        self.by_seg_uf_ = self._rates(d, ["segmento", "UF"])
        self.by_seg_ = self._rates(d, ["segmento"])
        self.by_uf_ = self._rates(d, ["UF"])
        return self

    def _rates(self, d: pd.DataFrame, keys: list[str]) -> pd.Series:
        g = d.groupby(keys)["y"].agg(["mean", "size"])
        return g[g["size"] >= self.min_cell]["mean"]

    def predict_proba(self, X):
        idx = pd.MultiIndex.from_frame(X[["segmento", "UF"]])
        p = pd.Series(self.by_seg_uf_.reindex(idx).to_numpy(), index=X.index)
        p = p.fillna(pd.Series(self.by_seg_.reindex(X["segmento"]).to_numpy(), index=X.index))
        p = p.fillna(pd.Series(self.by_uf_.reindex(X["UF"]).to_numpy(), index=X.index))
        p = p.fillna(self.global_).clip(1e-6, 1 - 1e-6)
        return np.column_stack([1 - p, p])


class MajorityClass(BaseEstimator, ClassifierMixin):
    """Predicts the training base rate for everyone. The floor any model must clear."""

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        self.rate_ = float(np.mean(y))
        return self

    def predict_proba(self, X):
        p = np.full(len(X), self.rate_)
        return np.column_stack([1 - p, p])


def preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)),
                          ("scale", StandardScaler())]), NUMERIC),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="constant", fill_value="missing")),
                          ("ohe", OneHotEncoder(handle_unknown="infrequent_if_exist",
                                                min_frequency=30, sparse_output=False))]),
         CATEGORICAL),
    ])


def temporal_folds(years: pd.Series) -> list[tuple[np.ndarray, np.ndarray]]:
    """Fit on every cohort before the validation year, validate on that year."""
    uniq = sorted(years.unique())
    folds = []
    for val_year in uniq[1:]:
        tr = np.where(years < val_year)[0]
        va = np.where(years == val_year)[0]
        if len(tr) and len(va):
            folds.append((tr, va))
    return folds


def metrics(y_true, p) -> dict:
    order = np.argsort(-p)
    top = order[: max(1, len(p) // 10)]
    base = float(np.mean(y_true))
    return {
        "pr_auc": float(average_precision_score(y_true, p)),
        "roc_auc": float(roc_auc_score(y_true, p)),
        "brier": float(brier_score_loss(y_true, p)),
        "lift_top_decile": float(np.mean(np.asarray(y_true)[top]) / base) if base else float("nan"),
        "base_rate": base,
        "n": int(len(p)),
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = build(pd.read_parquet("data/processed/projetos.parquet"))
    s = df[df["in_model_sample"]].reset_index(drop=True)
    train = s[s["split"] == "train"].reset_index(drop=True)
    test = s[s["split"] == "test"].reset_index(drop=True)
    log.info("train %d (cohorts %s), test %d (cohort %s)", len(train),
             sorted(train.ano_projeto.unique()), len(test), sorted(test.ano_projeto.unique()))

    cols = NUMERIC + CATEGORICAL
    Xtr, ytr = train[cols], train[TARGET].astype(int)
    Xte, yte = test[cols], test[TARGET].astype(int)
    folds = temporal_folds(train["ano_projeto"])
    log.info("temporal folds inside train: %d", len(folds))

    candidates = {
        "baseline_majority": MajorityClass(),
        "baseline_segment_uf_rate": SegmentUFRate(),
        "logistic": Pipeline([("prep", preprocessor()),
                              ("clf", LogisticRegression(max_iter=2000, C=1.0,
                                                         random_state=SEED))]),
        "lightgbm": Pipeline([("prep", preprocessor()),
                              ("clf", LGBMClassifier(random_state=SEED, verbose=-1,
                                                     n_estimators=400, learning_rate=0.05,
                                                     num_leaves=31, min_child_samples=40))]),
    }

    # Cross validated on the temporal folds inside train. This is what picks the model.
    cv_rows = []
    for name, est in candidates.items():
        scores = []
        for tr_idx, va_idx in folds:
            e = est.__class__(**est.get_params()) if not isinstance(est, Pipeline) else est
            from sklearn.base import clone
            e = clone(est)
            e.fit(Xtr.iloc[tr_idx], ytr.iloc[tr_idx])
            p = e.predict_proba(Xtr.iloc[va_idx])[:, 1]
            scores.append(metrics(ytr.iloc[va_idx], p))
        cv_rows.append({"model": name,
                        **{k: float(np.mean([s[k] for s in scores]))
                           for k in ("pr_auc", "roc_auc", "brier", "lift_top_decile")}})
    cv = pd.DataFrame(cv_rows).sort_values("pr_auc", ascending=False)
    log.info("cross validated on train:\n%s", cv.to_string(index=False))

    # Calibrate the chosen model on the same temporal folds, then score the test cohort
    # once. Nothing after this point changes any choice.
    best_name = cv.iloc[0]["model"]
    log.info("selected by CV PR-AUC: %s", best_name)
    from sklearn.base import clone
    calibrated = CalibratedClassifierCV(clone(candidates[best_name]), method="isotonic",
                                        cv=folds)
    calibrated.fit(Xtr, ytr)

    final = {}
    for name, est in candidates.items():
        e = clone(est).fit(Xtr, ytr)
        final[name] = metrics(yte, e.predict_proba(Xte)[:, 1])
    final[f"{best_name}_calibrated"] = metrics(yte, calibrated.predict_proba(Xte)[:, 1])

    res = pd.DataFrame(final).T.sort_values("pr_auc", ascending=False)
    log.info("held out cohort 2022, scored once:\n%s", res.to_string())

    REPORTS.mkdir(parents=True, exist_ok=True)
    cv.to_csv(REPORTS / "cv_results.csv", index=False)
    res.to_csv(REPORTS / "test_results.csv")
    (REPORTS / "model_selection.json").write_text(
        json.dumps({"selected": best_name, "folds": len(folds),
                    "train_n": len(train), "test_n": len(test)}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
