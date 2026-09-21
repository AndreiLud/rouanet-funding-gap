-- Sub-question 1, time dimension: how has the funding rate moved by approval cohort?
--
-- Deliberately reads every cohort, not just the analysable ones, and reports the share
-- of each cohort whose fundraising window is still open. Cohorts from 2023 onwards are
-- 22% to 90% open, and the projects that close first are disproportionately the ones
-- closed for raising nothing, so their apparent rate is biased downwards. The
-- `pct_window_open` column is what stops that artefact being read as a trend.

SELECT
    ano_projeto AS cohort,
    count(*) AS projetos,
    round(100.0 * avg(CASE WHEN window_state = 'open' THEN 1 ELSE 0 END), 1) AS pct_window_open,
    count(*) FILTER (WHERE in_model_sample) AS n_analysable,
    round(avg(target_gt0)  FILTER (WHERE in_model_sample), 4) AS rate_gt0,
    round(avg(target_ge20) FILTER (WHERE in_model_sample), 4) AS rate_ge20,
    round(avg(target_ge50) FILTER (WHERE in_model_sample), 4) AS rate_ge50,
    round(avg(target_ge100) FILTER (WHERE in_model_sample), 4) AS rate_ge100,
    round(sum(valor_captado) FILTER (WHERE in_model_sample)
          / nullif(sum(valor_aprovado) FILTER (WHERE in_model_sample), 0), 4) AS share_of_value_raised
FROM projetos
WHERE ano_projeto >= 2019
GROUP BY ano_projeto
ORDER BY ano_projeto;
