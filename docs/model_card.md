# Model card

## What it does

Estimates the probability that an approved Rouanet project raises at least 50% of the
amount it requested, using only information available at approval.

**The headline result is negative, and that is the finding.** A model built on
approval-time information does not beat a simple historical rate in any way that matters
for the decision this project serves. It ranks slightly better and prices much worse.

## Data

61,337 projects from the SALIC API, collected 2026-09-20, approval cohorts 2019 to 2026.
The analysable sample is 12,722 projects: cohorts 2019 to 2022, fundraising window
closed, requested amount above zero.

Cohorts from 2023 on are excluded because 22% to 90% of each is still raising money, and
the projects that close first are disproportionately the ones that closed empty, so
their apparent rate is biased downwards. Cohorts before 2019 do not exist in the API.

Split: train on 2019 to 2021 (10,102), test on 2022 (2,620). Tuning used time ordered
folds inside train only (fit 2019 validate 2020; fit 2019 and 2020 validate 2021).

## Results

Cross validated inside train:

| Model | PR-AUC | ROC-AUC | Brier | Lift, top decile |
| --- | --- | --- | --- | --- |
| Logistic regression | 0.666 | 0.768 | 0.185 | 1.98 |
| LightGBM | 0.658 | 0.768 | 0.197 | 1.88 |
| Heuristic: segment and state rate | 0.523 | 0.655 | 0.221 | 1.54 |
| Majority class | 0.394 | 0.500 | 0.239 | 1.33 |

Held out cohort 2022, scored once, base rate 0.437:

| Model | PR-AUC | ROC-AUC | Brier | Lift, top decile |
| --- | --- | --- | --- | --- |
| Logistic regression | 0.580 | 0.650 | **0.349** | 1.47 |
| LightGBM | 0.539 | 0.614 | 0.340 | 1.40 |
| Logistic, isotonic calibration | 0.534 | 0.627 | 0.321 | 1.42 |
| Heuristic: segment and state rate | 0.530 | 0.616 | **0.235** | 1.31 |
| Majority class | 0.437 | 0.500 | 0.249 | 0.92 |

Read the Brier column. The model's is worse than predicting the base rate for everyone.
It gains 0.05 of PR-AUC over the heuristic and gives up 0.11 of Brier score. For a
product whose whole output is a probability, that trade is a loss.

## Why it fails

The failure is the level, not the ranking. On the held out cohort the model predicts a
mean probability of 0.767 where 0.437 happened. The heuristic predicts 0.426. The
model's deciles still climb from 0.18 to 0.64 actual, so the ordering survives; every
one of them is priced too high.

The cause is drift in the proponent history features. Their missing rate falls from 77%
in train to 54% in test as the observation window lengthens, and the observed prior
success rate drifts upward (median 0.600 to 0.875) because proponents who appear
repeatedly are disproportionately the ones who succeeded. The feature means something
different in 2022 than it meant in 2020, and the model reads the difference as a better
cohort.

This is a property of a four cohort window on a data source that starts in 2019. With
more cohorts it could be corrected, for example by normalising the prior rate against
its own cohort. With four, any such fix is fitted to one transition and is not
trustworthy.

## What it must not be used for

- **Not for deciding whose project gets approved.** It predicts fundraising, not merit,
  and it is trained on a system whose money is highly concentrated. Using it to rank
  applicants would automate that concentration.
- **Not as a forecast for an individual project.** The largest determinant, whether the
  producer already has a sponsor in hand, is absent from the public data. What is here
  is a prior for projects that look alike on paper.
- **Not for cohorts still raising money.** Everything here is conditioned on a closed
  fundraising window.

## Fairness and concentration

The system this models is extremely concentrated: the top 10% of proponents took 83% of
the money raised in the analysable window, and on the sponsor side the top 10% account
for 98.4% of all donations ever recorded, with a Gini of 0.981. Any model trained on
these outcomes learns that concentration. The regional spread is large and the model
reproduces it: measured rates run from about 51% in Ceara to about 16% in Goias.

## Leakage

`valor_aprovado` is revised after the outcome and is excluded along with everything
derived from it. That exclusion is the single most consequential decision in the
project: with the revised field included, cross validated PR-AUC was 0.85 and a single
feature carried it. `docs/data_dictionary.md` has the evidence and the full exclusion
list.

## Reproducibility and honesty notes

Seeds are fixed in `src/config.py`. `requirements.txt` pins exact versions.
`make all` rebuilds everything downstream of the raw pages.

The test cohort was scored twice: once on the pipeline that still contained the leaked
field, and once after removing it. No model choice was made using either set of test
numbers, and the first run is void rather than reported. This is recorded here rather
than left for a reader to infer from the commit history.
