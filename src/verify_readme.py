"""Check that the numbers printed in the README are the numbers the pipeline produces.

The repository's rule is that every number in the README comes from executed code. That
rule is worth a test rather than a promise: a number can drift out of date the moment a
cleaning decision changes, and nothing else in the pipeline would notice.

Run with `make verify` after `make all`. It fails loudly if a claim no longer matches.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

from src.config import DATA_PROCESSED, DUCKDB_PATH, REPORTS, ROOT


def claims() -> list[tuple[str, str]]:
    df = pd.read_parquet(DATA_PROCESSED / "projetos.parquet")
    s = df[df["in_model_sample"]]
    r = s["share_raised"]
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    cat = con.execute((ROOT / "sql" / "q1_funding_rate_by_category.sql").read_text()).df()
    spon = con.execute((ROOT / "sql" / "q2b_concentration_sponsors.sql").read_text()).df().iloc[0]
    tipo = con.execute((ROOT / "sql" / "q3_pessoa_fisica_vs_juridica.sql").read_text()).df()
    con.close()
    pf = tipo[tipo.tipo == "pessoa fisica"].iloc[0]
    pj = tipo[tipo.tipo == "pessoa juridica"].iloc[0]
    test = pd.read_csv(REPORTS / "test_results.csv", index_col=0)

    def band(v):
        return cat[(cat.dimensao == "faixa_valor") & (cat.valor == v)].iloc[0]

    def uf(v):
        return cat[(cat.dimensao == "UF") & (cat.valor == v)].iloc[0]

    return [
        (f"{len(df):,}", "projects collected"),
        (f"{len(s):,}", "analysable projects"),
        (f"{int((r <= 0).sum()):,}", "raised nothing"),
        (f"{(r >= .5).mean()*100:.1f}%", "reached half the request"),
        (f"{s.valor_captado.sum()/s.valor_solicitado.sum()*100:.1f}%", "share of requested raised"),
        (f"{band('100k to 500k')['rate']*100:.1f}%", "rate, 100k to 500k"),
        (f"{int(band('100k to 500k')['n']):,}", "n, 100k to 500k"),
        (f"{band('under 100k')['rate']*100:.1f}%", "rate, under 100k"),
        (f"{band('5M and above')['rate']*100:.1f}%", "rate, 5M and above"),
        (f"{uf('GO')['rate']*100:.1f}%", "rate, GO"),
        (f"{uf('DF')['rate']*100:.1f}%", "rate, DF"),
        (f"{uf('CE')['rate']*100:.1f}%", "rate, CE"),
        (f"{uf('SC')['rate']*100:.1f}%", "rate, SC"),
        (f"{int(spon['incentivadores']):,}", "sponsors"),
        (f"{spon['top10pct_share']*100:.1f}%", "sponsor top decile share"),
        (f"{spon['top1pct_share']*100:.1f}%", "sponsor top percentile share"),
        (f"{spon['gini']:.3f}", "sponsor gini"),
        (f"{int(spon['n_pessoa_fisica']):,}", "individual sponsors"),
        (f"{test.loc['logistic', 'pr_auc']:.3f}", "logistic PR-AUC on test"),
        (f"{test.loc['logistic', 'brier']:.3f}", "logistic Brier on test"),
        (f"{test.loc['baseline_segment_uf_rate', 'pr_auc']:.3f}", "heuristic PR-AUC"),
        (f"{test.loc['baseline_segment_uf_rate', 'brier']:.3f}", "heuristic Brier"),
        (f"{test.loc['baseline_majority', 'pr_auc']:.3f}", "majority PR-AUC"),
        (f"{pf['pct_dos_projetos']:.1f}%", "share of projects, natural persons"),
        (f"{pf['pct_do_dinheiro']:.1f}%", "share of money, natural persons"),
        (f"{pf['taxa_zero']*100:.1f}%", "natural persons raising nothing"),
        (f"{pj['taxa_zero']*100:.1f}%", "organisations raising nothing"),
        (f"{pf['taxa_ge50']*100:.1f}%", "natural persons reaching half"),
        (f"{pj['taxa_ge50']*100:.1f}%", "organisations reaching half"),
    ]


def main() -> int:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = []
    for value, label in claims():
        present = value in readme
        print(f"  {'OK ' if present else 'MISS'}  {value:>14}   {label}")
        if not present:
            missing.append((value, label))

    referenced = []
    import re
    for m in set(re.findall(r"\]\(([^)]+)\)", readme)) | set(re.findall(r"`([^`\n]+)`", readme)):
        m = m.strip()
        if m.startswith("http") or " " in m:
            continue
        if "/" in m or m.endswith((".md", ".py", ".txt", ".ipynb")):
            referenced.append(m)
    broken = [p for p in sorted(set(referenced)) if not (ROOT / p.rstrip("/")).exists()]
    print(f"\n  {len(set(referenced))} referenced paths, {len(broken)} broken")

    if missing or broken:
        print("\nFAILED")
        for v, l in missing:
            print(f"  README does not contain {v} ({l})")
        for p in broken:
            print(f"  README references a path that does not exist: {p}")
        return 1
    print("\nOK: every checked number appears in the README and every path exists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
