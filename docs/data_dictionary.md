# Data dictionary

Source: SALIC API, `https://api.salic.cultura.gov.br/api/v1`, collected 2026-09-20.
Field names keep the API's own spelling on ingest, including its two typos, and are
renamed once at the processed boundary so a row can always be traced back to a raw page.

## What the API returns for a project

| Field | Type | Notes |
| --- | --- | --- |
| `PRONAC` | str | Project identifier. Unique across the 61,337 rows collected. |
| `nome` | str | Project name. Not used. |
| `proponente` | str | Proponent name. **Never leaves `data/raw`.** |
| `cgccpf` | str | CPF or CNPJ. **Never leaves `data/raw`.** |
| `situacao` | str | Current administrative status, 66 distinct values. |
| `providencia` | str | Free text. Used only as a character count. |
| `UF`, `municipio` | str | Location of the proponent. |
| `local_realizacao` | list | Municipalities where the project happens, with IBGE codes. Reduced to a count. |
| `segmento`, `tipicidade`, `tipologia` | str | Classification. 123, 18 and 113 distinct values. |
| `enquadradmento` | str | The API spells it this way. Renamed to `enquadramento`. |
| `mecanisnmo` | str | The API spells it this way. Renamed to `mecanismo`. |
| `ano_projeto` | str | Two digit approval year. The live docs define it as the year the project was approved. |
| `data_inicio`, `data_termino` | str | Execution window, not the fundraising window. |
| `valor_solicitado` | num | Amount requested at submission. |
| `valor_proposta` | num | Proposal value. Identical to `valor_solicitado` in 94.3% of rows. |
| `valor_aprovado` | num | Approved amount. **Revised after the outcome, see below.** |
| `valor_projeto` | num | `valor_aprovado` plus `outras_fontes`. Inherits the revision. |
| `valor_captado` | num | Amount actually raised. The outcome. |
| `outras_fontes` | num | Other declared funding. Zero in about 94% of rows. |
| Free text blocks | str | `objetivos`, `justificativa`, `resumo`, `sinopse`, `etapa`, `ficha_tecnica`, `acessibilidade`, `democratizacao`, `impacto_ambiental`, `especificacao_tecnica`, `estrategia_execucao`. Reduced to character counts. |

`area` is **not** in the payload although it is a valid query parameter, so it is
recovered by sweeping the 8 area codes and tagging each record with the code it was
requested under. The 8 counts sum to exactly 61,337, so the sweep is a partition.

## Excluded from the model, and why

| Field | Why it is out |
| --- | --- |
| `valor_captado` | It is the target. |
| `valor_aprovado`, `valor_projeto`, and anything derived from them | **Revised after the outcome.** The approved amount is adjusted during the accounting phase to match what was raised: it is revised for 31.7% of projects that raised money and 1.3% of those that did not, and the revisions concentrate in the prestacao de contas statuses (43.1% of `Prestacao de Contas Aprovada`, 0.8% of `encerrado por excesso de prazo sem captacao`). A first version of this model used approved over requested as a feature, and permutation importance gave it 0.271 against 0.012 for the next feature: it was reading the outcome. |
| `situacao` | Settled after the fact. It is used to decide **who is in the sample** and never as a feature. That distinction holds: a variable settled after the fact can define the analysable universe without being allowed to predict within it. |
| `providencia` | A post-hoc administrative note. Only its length is kept, and even that is a judgement call. |
| Extension records, payment and audit blocks | Only exist after the window, and only for projects that got somewhere. |
| `total_captado` on the proponent record | A lifetime total that already contains the outcome being predicted. |
| Anything from the sponsor side | Only exists once money has moved. |
| `proponente`, `cgccpf` | LGPD. Replaced by a salted hash that never leaves `data/interim` onwards, and dropped entirely from the app artefact. |

## The target

`target_ge50` is `valor_captado / valor_solicitado >= 0.5`.

The denominator is the **requested** amount, not the approved amount, for the reason in
the table above: a share of a revised approved amount is partly a function of its own
numerator. It is also the quantity the producer actually controls when sizing a budget,
which is the decision this project informs.

The headline is not sensitive to the choice. Pooled over cohorts 2019 to 2022:

| Denominator | Raised nothing | Reached 50% | Reached 100% |
| --- | --- | --- | --- |
| `valor_solicitado` (used) | 50.0% | 39.5% | 8.8% |
| `valor_aprovado` | 50.0% | 39.9% | 6.6% |
| `valor_proposta` | 50.0% | 39.2% | 8.3% |

Thresholds at more than 0%, 20%, 50% and 100% are all computed and reported. 50% is the
headline because that is where the curve has a step: 50.0% raise something, 46.8% reach
20%, 39.5% reach 50%, and 8.8% reach the full amount. Between "raised anything" and
"reached 20%" the rate barely moves, because a project that raises at all usually gets
past a fifth. The real separation is at half.

## Features actually used

Numeric: `valor_solicitado_log`, `outras_fontes_log`, `n_municipios`, `duracao_dias`,
and character counts for seven text blocks. Proponent history: `prior_projetos`,
`prior_taxa_ge50`, `prior_captado_log`.

Categorical: `area`, `segmento`, `tipicidade`, `tipologia`, `UF`, `mecanismo`,
`enquadramento`.

**Proponent history is strictly backward looking.** For each approval cohort, history is
built only from cohorts before it, so a 2021 project sees 2019 and 2020 and nothing
else. A proponent seen for the first time gets a missing value rather than a zero,
because "no track record" and "a track record of nothing" are different states. The
availability of history by cohort is 0% for 2019, 27.0% for 2020, 42.0% for 2021 and
45.8% for 2022, which is what a backward looking window should look like.

The same feature carries a known defect: because the observation window lengthens, its
distribution drifts, and that drift is what breaks the model's calibration on the held
out cohort. See `docs/model_card.md`.
