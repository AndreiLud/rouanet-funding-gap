# Project brief

**Approved is not funded: who actually raises money through Brazil's Rouanet Law**

Status: contract verified against the live API on 2026-09-20. The counts in section 3
were produced by querying the API, not estimated. No modelling result exists yet.

## 1. The decision

Brazil's Rouanet Law works in two steps. MinC approves a project and an amount
(`valor_aprovado`), and that approval brings no money: it only gives the producer
permission to find sponsors (`incentivadores`) who redirect part of their income tax
into the project. Many approved projects raise little or nothing.

Who decides with the answer: the cultural producer, sizing a budget and deciding whether
to submit at all. Secondary reader: MinC, looking at how concentrated fundraising is
across proponents, sponsors and states.

The question: **for an approved project, what is the probability of raising at least X%
of the approved amount, using only what is known at approval time?**

## 2. Sub-questions

1. Funding rate by area, segment, UF and value band, and how it moved over time.
2. How concentrated fundraising is, across proponents and across sponsors.
3. Does a model using approval-time information beat a simple rule (the historical rate
   of that segment in that UF)?
4. Where does the model fail hardest?

## 3. Data source and contract (verified live, 2026-09-20)

SALIC API, open, no authentication. Base URL `https://api.salic.cultura.gov.br`,
base path `/api/v1`. The live API is a Laravel rewrite documented with Scribe at
`/docs` (last updated 2026-09-14), not the Flask service whose OpenAPI spec is still
published in the old public source repository. The differences below were found by
querying the live service, and they are the reason the earlier draft of this section was
wrong.

Endpoints used: `/api/v1/projetos`, `/api/v1/projetos/areas`,
`/api/v1/projetos/segmentos`, `/api/v1/proponentes`, `/api/v1/incentivadores`.

**Path form.** Requests must omit the trailing slash. `/api/v1/projetos/` answers 301 to
the same path over plain HTTP, which is both a downgrade and unreachable from a
proxied environment. `/v1/projetos` (the old base path) answers 404.

**Coverage.** The service holds 61,337 projects, and they are not the full history of the
law. Counting by `ano_projeto`: 2019 has 3,508, 2020 has 4,683, 2021 has 2,645, 2022 has
2,681, 2023 has 10,722, 2024 has 14,215, 2025 has 15,415, 2026 has 7,466, plus one
record each in 2016 and 2018. Those sum to 61,337, the reported total. Every year before
2019 answers `{"message": "No project was found with your criteria", "message_code": 11}`.
The analysis window is therefore 2019 to 2026, not the 1990s onwards.

**Fields returned by `/api/v1/projetos`** (35 keys, present on all 100 records of a
sampled page): `PRONAC`, `nome`, `proponente`, `cgccpf`, `situacao`, `providencia`,
`UF`, `municipio`, `local_realizacao` (a list of municipalities with IBGE codes),
`segmento`, `tipicidade`, `tipologia`, `enquadradmento`, `mecanisnmo`, `ano_projeto`,
`data_inicio`, `data_termino`, `valor_solicitado`, `valor_aprovado`, `valor_projeto`,
`valor_captado`, `valor_proposta`, `outras_fontes`, the free text blocks
(`objetivos`, `justificativa`, `resumo`, `sinopse`, `etapa`, `ficha_tecnica`,
`acessibilidade`, `democratizacao`, `impacto_ambiental`, `especificacao_tecnica`,
`estrategia_execucao`), and `_links`.

`enquadradmento` and `mecanisnmo` are spelled that way by the API. The field names are
kept verbatim on ingest and renamed only in the processed layer, so that a raw page can
always be traced back.

**`area` is not in the payload.** The old contract returned it; the live one does not,
although `area` still works as a query parameter. It is recovered by sweeping the 8 area
codes from `/api/v1/projetos/areas` (Artes Cenicas 18,677, Audiovisual 6,301, Musica
17,363, Artes Visuais 6,776, Patrimonio Cultural 1,970, Humanidades 8,722, Artes
Integradas 324, Museus e Memoria 1,204) and tagging each record with the code used in the
request. Those counts sum to exactly 61,337, so the sweep is a partition: no project is
missed and none is fetched twice.

**`ano_projeto` is the approval year.** The live documentation defines it as "ano em que o
projeto foi aprovado", where the old spec said the year it was submitted. This is the
cohort variable, and it is still two digits.

**Pagination.** `limit` in [1, 100], `offset` in [0, total]. The body carries `count` (rows
in this response) and `total` (rows matching the query). The documented `X-Total-Count`
header was not present on the responses observed, so pagination is driven by the body's
`total`. At `limit=100` the full sweep is 614 pages.

**Other parameters**: `PRONAC`, `proponente`, `proponente_id`, `cgccpf`, `nome`, `area`,
`segmento`, `UF`, `ano_projeto`, `data_inicio`, `data_termino` and their `_min` and
`_max` forms, `ano_captacao` (an integer year derived from the receipt date `DtRecibo`),
`sort` (default `ano_projeto:desc`) and `format` (HAL+JSON by default, also XML and CSV).

**Volume.** A sampled page averages 28,562 bytes per record, dominated by the free text
blocks, so the full pull is about 1.6 GB of JSON. Raw pages are stored gzipped, which
keeps them byte for byte as received while fitting the disk budget.

## 4. Target

Target: `valor_captado >= X% of valor_aprovado`.

Proposed headline X is 50%. Below roughly half the approved budget a project usually
cannot be delivered as approved and has to be rescoped, so 50% matches the producer's
real question ("can I actually do this?"). More than 0% is a bar a single token donation
clears; 100% is a different question. The sensitivity curve (more than 0%, 20%, 50%, and
the continuous share captured) is reported alongside, and X is confirmed against the
observed distribution in step 2 before being fixed.

## 5. Censoring

Recent projects are still inside their fundraising window, so their `valor_captado` is
not final and reads as failure.

The live data settles this better than the percentile rule in the earlier draft, because
`situacao` states the outcome of the window directly. Values such as "Projeto encerrado
por excesso de prazo sem captacao" mark a window that closed with nothing raised, while
"Autorizada a captacao total dos recursos" marks one that is still open. A cohort is
included when its projects have reached a terminal `situacao`, and the share of
non-terminal cases per cohort is reported so the reader can see where the window is
still closing.

This uses `situacao` to decide **who is in the sample**, never as a feature. That
distinction is the one that has to hold: a variable settled after the fact can define the
analysable universe without being allowed to predict within it. The rule and the terminal
value list go in `docs/data_dictionary.md`, and the cutoff is cross checked against the
`ano_captacao` filter, which reports fundraising activity by receipt year.

The cost is severe and has to be stated: with coverage starting in 2019 and the most
recent cohorts still open, only a handful of approval cohorts are usable, so the temporal
split is thin and 2020 and 2021 sit inside it. Section 11 carries the consequence.

## 6. Leakage rules

In: `valor_aprovado`, `valor_solicitado`, `valor_proposta`, `outras_fontes`, `area`
(recovered by the sweep), `segmento`, `tipicidade`, `tipologia`, `UF`, `municipio`
(grouped), number of municipalities in `local_realizacao`, `mecanisnmo`,
`enquadradmento`, cohort year, project duration as declared at approval, and proponent
history features. The last two field names carry the API's own spelling.

Out, with the reason recorded per field in `docs/data_dictionary.md`: `valor_captado`
(it is the target), `situacao` (current status, settled after the fact), anything from
the sponsor side, extension records (`prorrogacao`, only granted later), payment and
audit blocks from the detail endpoint, and `total_captado` on the proponent record (it
is a lifetime total that already contains the outcome we are predicting). `valor_projeto`
is dropped as a deterministic function of `valor_aprovado` and `outras_fontes`, which is
collinearity rather than leakage.

Proponent history is computed from strictly earlier cohorts only, using an expanding
window, and for a proponent's first project the history features are explicitly missing
rather than zero, because "no track record" and "a track record of zero" are different
states.

## 7. Validation and metrics

Split is temporal by cohort: train on older cohorts, test on the most recent cohorts
whose window is closed. Tuning uses time ordered cross validation inside the training
years only, and the test set is scored once, at the end.

Baselines first: majority class, then the heuristic the producer could apply unaided,
the historical rate for that segment in that UF. The models are logistic regression and
LightGBM, both inside a scikit-learn `Pipeline` with a `ColumnTransformer` so that
preprocessing is fitted inside each fold.

Metrics: PR-AUC (unbalanced classes, positive class is what matters), Brier score and a
calibration curve (the app shows a probability, so being right at each probability level
matters more than ranking), and lift in the top decile. Error analysis by area, UF and
value band, plus permutation importance or SHAP, labelled as association and not cause.

Structural breaks (the 2020 to 2021 pandemic years, and rule changes over the period) are
tested rather than asserted: cohort by cohort rates are plotted, the model is scored
separately on the affected cohorts, and whatever the data shows is what gets written.

## 8. Concentration

Proponent side, from the full project table: share of total captured by the top 10% of
proponents, and Gini or HHI per cohort year. Sponsor side, from `/incentivadores/`:
the same shares on `total_doado`. That sponsor cross section has no time dimension, so
per year sponsor concentration would need the `doacoes` endpoint for every sponsor,
which is a much heavier pull. The limitation is stated rather than patched with a
biased top K sample. Natural persons appear only inside aggregates, identified by a
salted hash, never by name.

## 9. Collection

`api.salic.cultura.gov.br` and `dados.cultura.gov.br` were added to the environment's
allowed domains on 2026-09-20, and the contract in section 3 was verified against the
live service. The earlier blocker is cleared.

Collection sweeps the 8 area codes, writes one gzipped raw page per request under
`data/raw/` named with endpoint, area, offset and collection date, honours `Retry-After`,
backs off exponentially on 5xx, and resumes by skipping pages already on disk.

## 10. Deliverables

`notebooks/` 01 collection, 02 EDA, 03 modelling, 04 error analysis. `sql/` one file per
sub-question over DuckDB. `src/` collector, cleaning, features, modelling. `app/` a
Streamlit app where a producer picks area, segment, UF and value band and sees the
historical rate for comparable projects with a confidence interval and a sample size,
the calibrated model probability, and the limitations in plain language.
`docs/` this brief, the data dictionary, the cleaning log and the model card.
`make all` reproduces everything from the raw pages.

## 11. What would make this project wrong

The coverage window is the binding constraint. The API starts at approval year 2019, so
"how it changed over time" spans 2019 to 2026 and not the history of the law, and once
the open cohorts are removed only a few remain to train and test on. Those few include
2020 and 2021, so a pandemic effect and a cohort effect cannot be cleanly separated:
this is reported as a limitation, not modelled away.

The cohort rule leans on `situacao`, which is a settled administrative status and can be
stale or inconsistent, so a wrong terminal list mislabels late fundraisers as failures.
Records with `valor_captado` above `valor_aprovado` exist and reach large multiples, so
the impossible-value check is not a formality and whatever it finds goes in the cleaning
log rather than being silently clipped.

Approval-time information is thin: no evaluation score, no committee decision, no sponsor
pipeline, so a producer's real advantage (who they already know) is invisible here and the
model can only be a prior, not a forecast. The app says this in plain words.
