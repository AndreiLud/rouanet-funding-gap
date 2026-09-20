# Project brief

**Approved is not funded: who actually raises money through Brazil's Rouanet Law**

Status: written before collection. Section 9 records a blocker that has to be cleared
before any data can be pulled. No number in this document comes from data, because no
data has been collected yet.

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

## 3. Data source and contract

SALIC API, open, no authentication. Host `api.salic.cultura.gov.br`, basePath `/v1`,
spec version 0.2.1-beta.

Endpoints used: `/projetos/` (list), `/projetos/{PRONAC}` (detail),
`/projetos/areas`, `/projetos/segmentos`, `/proponentes/`, `/incentivadores/`,
`/incentivadores/{id}/doacoes`.

Fields returned by `/projetos/` (`ProjetoList`): `PRONAC`, `ano_projeto`, `nome`,
`cgccpf`, `proponente`, `segmento`, `area`, `UF`, `municipio`, `data_inicio`,
`data_termino`, `situacao`, `mecanismo`, `enquadramento`, `valor_projeto`,
`outras_fontes`, `valor_captado`, `valor_proposta`, `valor_solicitado`,
`valor_aprovado`, plus free text fields (`objetivos`, `justificativa`, `sinopse`,
`resumo`, and others).

`Proponente`: `nome`, `cgccpf`, `responsavel`, `tipo_pessoa`, `UF`, `municipio`,
`total_captado`. `Incentivador`: same shape with `total_doado`. `Doacao` and `Captacao`:
`PRONAC`, `valor`, `data_recibo`, `nome_projeto`, `cgccpf`, `nome_doador`.

Collection mechanics, as specified:

- Pagination is `limit` and `offset`. `limit` defaults to 100 and is capped at 100
  (`LIMIT_PAGING`); asking for more returns an error rather than more rows.
- The total row count comes from the `X-Total-Count` response header.
- The `next` link in the HAL `_links` block advances the offset by 1 instead of by the
  page size, so pagination is driven by our own offset arithmetic against
  `X-Total-Count`, not by following links.
- Rate limiting is announced through `X-Rate-Limit-Limit`,
  `X-Rate-Limit-Remaining`, `X-Rate-Limit-Reset` and `Retry-After`. The collector
  honours `Retry-After` and backs off exponentially on 5xx.
- Every page is written to `data/raw/` as received, named with endpoint, offset and
  collection date. Collection resumes by skipping pages already on disk.

Three things about this contract are worth stating plainly. First, `ano_projeto` is a
two digit year, so the century has to be reconstructed (the law dates from the 1990s, so
93 to 99 maps to 19xx and 00 onwards to 20xx). Second, `data_inicio` and `data_termino`
are the project's execution window, not the fundraising window, and no approval date and
no fundraising deadline are exposed by the list endpoint. Third, `valor_aprovado` and
`valor_projeto` are computed server side and are defined differently for the agreement
mechanisms (`mecanismo` 2 and 6), where `valor_projeto` equals the approved agreement
value instead of approved plus other sources. Those mechanisms are flagged and analysed
separately.

**Verification caveat.** This contract was read from the OpenAPI specification and query
code published in the API's own source repository, because the live host is not
reachable from this environment (section 9). The published snapshot is from 2018, so
before any of it is used, every endpoint, parameter and field above is re-checked against
a live response, and `docs/data_dictionary.md` is written from observed responses rather
than from the spec. Any field that does not survive that check is removed from the plan,
not worked around.

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
not final and reads as failure. Since the API exposes no fundraising deadline, the
window has to be established empirically: for a random sample of projects we pull
`/projetos/{PRONAC}` and measure, from the `captacoes` block, the distribution of
(year of last `data_recibo` minus `ano_projeto`). The cohort cutoff is set at a high
percentile of that distribution, and the analysis keeps only cohorts whose window is
closed by that rule.

That is the primary approach: it matches the producer's binary decision and keeps the
model simple. The cost is that it discards the most recent years, which is exactly where
regime changes are most interesting, and the cutoff is a modelling choice rather than a
documented rule. The alternative, treating this as time to event with right censoring,
is noted in the model card as the natural extension and is not the headline model.

## 6. Leakage rules

In: `valor_aprovado`, `valor_solicitado`, `valor_proposta`, `outras_fontes`, `area`,
`segmento`, `UF`, `municipio` (grouped), `mecanismo`, `enquadramento`, cohort year,
project duration as declared at approval, and proponent history features.

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

## 9. Blocker: no network access to the data source

`api.salic.cultura.gov.br`, `salic.cultura.gov.br`, `dados.cultura.gov.br` and
`dados.gov.br` are all refused by this environment's egress policy (the proxy returns
403 on CONNECT, so no request reaches the API). Collection cannot start, and no number
in this repository can be produced, until that host is allowed. The options are to add
the host to the environment's allowed domains, or to run the collector outside this
environment and bring the raw pages in.

## 10. Deliverables

`notebooks/` 01 collection, 02 EDA, 03 modelling, 04 error analysis. `sql/` one file per
sub-question over DuckDB. `src/` collector, cleaning, features, modelling. `app/` a
Streamlit app where a producer picks area, segment, UF and value band and sees the
historical rate for comparable projects with a confidence interval and a sample size,
the calibrated model probability, and the limitations in plain language.
`docs/` this brief, the data dictionary, the cleaning log and the model card.
`make all` reproduces everything from the raw pages.

## 11. What would make this project wrong

The cohort cutoff is inferred, not documented, so a wrong cutoff mislabels late
fundraisers as failures. `valor_aprovado` is computed server side and defined differently
by mechanism. Approval-time information is thin: no evaluation score, no committee
decision, no sponsor pipeline, so a producer's real advantage (who they already know) is
invisible here and the model can only be a prior, not a forecast. The app says this in
plain words.
