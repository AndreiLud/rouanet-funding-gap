"""Data quality checklist over the parsed project table.

Prints a report and writes reports/quality_report.md. It decides nothing: every
finding here becomes an explicit, logged decision in docs/cleaning_log.md.

The integrity check is the one that is easy to skip and expensive to get wrong. The
API paginates by offset over a live table sorted by ano_projeto:desc, so if rows are
inserted while a sweep runs, later pages shift and records are duplicated or missed.
Comparing distinct PRONACs collected per area against the total the API reported at
the start of that area's sweep is what catches it.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import DATA_INTERIM, REPORTS

log = logging.getLogger("quality")

UFS = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT",
    "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}


def _section(title: str, body: str) -> str:
    return f"\n## {title}\n\n{body}\n"


def run(df: pd.DataFrame) -> str:
    out = ["# Data quality report", "",
           f"Rows parsed: {len(df):,}. Columns: {df.shape[1]}."]

    # 1. Identity and duplicates
    n_unique = df["PRONAC"].nunique()
    dupes = df[df.duplicated("PRONAC", keep=False)]
    dupe_across_area = (
        dupes.groupby("PRONAC")["_source_area"].nunique().gt(1).sum() if len(dupes) else 0
    )
    out.append(_section("Identity", "\n".join([
        f"- Distinct PRONAC: {n_unique:,}",
        f"- Rows that share a PRONAC with another row: {len(dupes):,}",
        f"- PRONACs appearing under more than one area code: {dupe_across_area:,}",
    ])))

    # 2. Collection integrity against what the API reported
    integ = []
    for area, grp in df.groupby("_source_area"):
        integ.append(f"- area {area}: {grp['PRONAC'].nunique():,} distinct PRONAC collected")
    out.append(_section("Collection integrity", "\n".join(integ)))

    # 3. Nulls
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0].sort_values(ascending=False)
    body = "\n".join(f"- `{c}`: {v:,} ({v/len(df):.1%})" for c, v in nulls.items())
    out.append(_section("Missing values", body or "No nulls in any column."))

    # 4. Impossible or suspicious values
    money = ["valor_solicitado", "valor_aprovado", "valor_projeto", "valor_captado",
             "valor_proposta", "outras_fontes"]
    checks = []
    for c in money:
        neg = (df[c] < 0).sum()
        if neg:
            checks.append(f"- `{c}` negative: {neg:,}")
    approved = df[df["valor_aprovado"] > 0]
    over = approved[approved["valor_captado"] > approved["valor_aprovado"]]
    checks.append(f"- approved projects (valor_aprovado > 0): {len(approved):,}")
    checks.append(f"- captado above aprovado: {len(over):,} ({len(over)/max(len(approved),1):.1%} of approved)")
    if len(over):
        ratio = (over["valor_captado"] / over["valor_aprovado"])
        checks.append(f"  - ratio median {ratio.median():.2f}, max {ratio.max():.1f}")
        checks.append(f"  - above 2x approved: {(ratio > 2).sum():,}")
    checks.append(f"- valor_aprovado == 0: {(df['valor_aprovado'] == 0).sum():,}")
    checks.append(f"- valor_aprovado == 0 but valor_captado > 0: "
                  f"{((df['valor_aprovado'] == 0) & (df['valor_captado'] > 0)).sum():,}")
    out.append(_section("Impossible and suspicious values", "\n".join(checks)))

    # 5. Categories
    bad_uf = sorted(set(df["UF"].dropna().unique()) - UFS)
    cats = [
        f"- distinct UF: {df['UF'].nunique()} (outside the 27 federal units: {bad_uf or 'none'})",
        f"- distinct segmento: {df['segmento'].nunique()}",
        f"- distinct area: {df['area'].nunique()}",
        f"- distinct tipologia: {df['tipologia'].nunique()}",
        f"- distinct tipicidade: {df['tipicidade'].nunique()}",
        f"- distinct mecanismo: {df['mecanismo'].nunique()}",
        f"- distinct enquadramento: {df['enquadramento'].nunique()}",
    ]
    out.append(_section("Categories", "\n".join(cats)))

    # 6. Cohort coverage
    cov = df.groupby("ano_projeto").agg(
        projetos=("PRONAC", "nunique"),
        aprovados=("valor_aprovado", lambda s: int((s > 0).sum())),
    )
    body = "\n".join(f"- {int(y)}: {r.projetos:,} projects, {r.aprovados:,} with valor_aprovado > 0"
                     for y, r in cov.iterrows())
    out.append(_section("Cohort coverage", body))

    # 7. Situacao, which decides who is in the analysable sample
    sit = df["situacao"].value_counts()
    body = "\n".join(f"- {v:,}  {k}" for k, v in sit.items())
    out.append(_section(f"Situacao values ({len(sit)} distinct)", body))

    return "\n".join(out)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = pd.read_parquet(DATA_INTERIM / "projetos.parquet")
    report = run(df)
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / "quality_report.md"
    path.write_text(report, encoding="utf-8")
    print(report)
    log.info("wrote %s", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
