"""Will this project raise the money? A calculator for cultural producers.

The number the app leads with is the historical rate for comparable projects, not the
model. That is a deliberate choice backed by the evaluation: on the held out cohort the
model ranks slightly better and prices much worse, and this app shows a probability
rather than a ranking. The model probability is shown second, with what is wrong with
it stated next to it.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"
HIGHLIGHT = "#2a78d6"

st.set_page_config(page_title="Approved is not funded", page_icon="//", layout="centered")


@st.cache_data
def load():
    sample = pd.read_csv(DATA / "sample.csv")
    meta = json.loads((DATA / "model_meta.json").read_text(encoding="utf-8"))
    return sample, meta


@st.cache_resource
def load_model():
    return joblib.load(DATA / "model.joblib")


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval. Used instead of the normal approximation because the
    cells a producer picks are often small, where a normal interval runs outside
    [0, 1] and reads as false precision."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def band(v: float) -> str:
    edges = [(1e5, "Under 100k"), (5e5, "100k to 500k"), (1e6, "500k to 1M"),
             (5e6, "1M to 5M"), (float("inf"), "5M and above")]
    for hi, label in edges:
        if v < hi:
            return label
    return edges[-1][1]


def add_band(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(faixa=df["valor_solicitado"].map(band))


sample, meta = load()
sample = add_band(sample)

st.title("Approved is not funded")
st.caption(
    f"In Brazil's Rouanet Law, approval is permission to go and find sponsors, not money. "
    f"Of {meta['n_total']:,} approved projects from {meta['cohorts'][0]} to {meta['cohorts'][-1]} "
    f"whose fundraising window has closed, half raised nothing at all."
)

with st.sidebar:
    st.header("Your project")
    area = st.selectbox("Area", meta["areas"])
    segmentos = meta["segmentos_by_area"].get(area, [])
    segmento = st.selectbox("Segment", segmentos) if segmentos else None
    uf = st.selectbox("State (UF)", meta["ufs"])
    valor = st.number_input("Amount you would request (R$)", min_value=10_000,
                            max_value=50_000_000, value=300_000, step=50_000)
    st.divider()
    st.caption("Optional: your track record, if you have run Rouanet projects before.")
    n_prev = st.number_input("Projects you have had approved before", 0, 50, 0)
    n_ok = st.number_input("...of those, how many raised at least half", 0, 50, 0,
                           disabled=n_prev == 0)

faixa = band(valor)

# 1. The historical rate for comparable projects, narrowing until the cell is usable.
levels = [
    ("segment, state and size", (sample.segmento == segmento) & (sample.UF == uf) & (sample.faixa == faixa)),
    ("segment and state", (sample.segmento == segmento) & (sample.UF == uf)),
    ("area, state and size", (sample.area == area) & (sample.UF == uf) & (sample.faixa == faixa)),
    ("area and size", (sample.area == area) & (sample.faixa == faixa)),
    ("area", sample.area == area),
    ("everything", pd.Series(True, index=sample.index)),
]
MIN_N = 30
for label, mask in levels:
    subset = sample[mask]
    if len(subset) >= MIN_N:
        break

n, k = len(subset), int(subset["target_ge50"].sum())
rate = k / n
lo, hi = wilson(k, n)

st.subheader("What happened to projects like yours")
c1, c2 = st.columns([1, 1.5])
c1.metric("Raised at least half of what they asked for", f"{rate*100:.0f}%")
c2.markdown(
    f"**95% confidence interval:** {lo*100:.0f}% to {hi*100:.0f}%  \n"
    f"**Based on:** {n:,} projects matched on *{label}*"
)
if label in ("area", "everything"):
    st.warning(
        f"There were fewer than {MIN_N} closed projects matching your exact segment, "
        f"state and size, so this rate is computed on a wider group ({label}). Treat it "
        f"as a rough prior, not as a rate for your situation."
    )

st.progress(rate)
st.caption(
    f"Median share of the request actually raised in this group: "
    f"{subset['share_raised_capped'].median()*100:.0f}%. "
    f"{(subset['share_raised_capped'] <= 0).mean()*100:.0f}% of them raised nothing."
)

# 2. The model, second, with its problem stated next to it.
st.subheader("What the model says")
model = load_model()
row = dict(meta["fill_values"])
row.update({
    "area": area, "segmento": segmento or meta["segmentos_by_area"][area][0], "UF": uf,
    "valor_solicitado_log": float(np.log1p(valor)),
    "prior_projetos": float(n_prev) if n_prev else np.nan,
    "prior_taxa_ge50": (n_ok / n_prev) if n_prev else np.nan,
})
X = pd.DataFrame([row])
p = float(model.predict_proba(X)[0, 1])
st.metric("Model probability of raising at least half", f"{p*100:.0f}%")
st.error(
    f"**Read this before using that number.** On the most recent cohort the model could "
    f"be tested against, it predicted an average of {meta['test_mean_predicted']*100:.0f}% "
    f"when {meta['test_actual_rate']*100:.0f}% actually happened. It orders projects from "
    f"more to less likely reasonably well, and it is too optimistic about all of them. "
    f"The historical rate above is the better number to plan with."
)
with st.expander("What the model was not told"):
    st.write(
        "You supplied " + ", ".join(f"`{c}`" for c in meta["user_supplied"]) + ". "
        "Everything else it uses is filled with the median of the training data, "
        "because a producer cannot know it while sizing a budget: "
        + ", ".join(f"`{c}`" for c in meta["filled_with_median"]) + "."
    )

st.subheader("What this cannot tell you")
st.markdown(
    f"""
- **The single biggest factor is missing.** Whether you already know a sponsor is the
  thing that decides most of this, and it is nowhere in the public data. The model can
  only give you a prior for projects that look like yours on paper.
- **The data starts in {meta['cohorts'][0]}.** The API exposes no approval cohort before
  then, so none of this describes the law's earlier decades, and a proponent active
  before {meta['cohorts'][0]} looks like a newcomer here.
- **Only closed cohorts are counted.** Projects from {meta['cohorts'][-1] + 1} onwards are
  still raising money, and counting them would make everything look far worse than it is.
- **Approval amounts get revised after the fact**, so every rate here is measured against
  what was *requested*, not against the approved amount.
- **This is association, not advice.** Nothing here says that changing your budget band
  changes your odds. It says projects in that band had those odds.
"""
)
st.caption(
    f"Source: SALIC API (api.salic.cultura.gov.br), collected {meta['collected_on']}. "
    f"Code and method: see the repository README and docs/model_card.md."
)
