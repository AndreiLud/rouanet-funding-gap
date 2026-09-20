-- Sub-question 1: what is the funding rate by area, segment, UF and value band?
-- Runs against data/processed/rouanet.duckdb. The `analysable` view is already
-- restricted to cohorts 2019 to 2022 with a closed fundraising window and an approved
-- amount above zero, which is the only sample where a rate can be read honestly.
--
-- The Wilson interval is used rather than the normal approximation because many cells
-- are small, and a normal interval on a proportion near 0 or 1 in a cell of 30 projects
-- produces bounds outside [0, 1].

WITH banded AS (
    SELECT
        area,
        segmento,
        UF,
        CASE
            WHEN valor_aprovado <   100000 THEN 'under 100k'
            WHEN valor_aprovado <   500000 THEN '100k to 500k'
            WHEN valor_aprovado <  1000000 THEN '500k to 1M'
            WHEN valor_aprovado <  5000000 THEN '1M to 5M'
            ELSE '5M and above'
        END AS faixa_valor,
        target_ge50
    FROM analysable
),
by_dimension AS (
    SELECT 'area'        AS dimensao, area        AS valor, count(*) AS n, sum(target_ge50) AS k FROM banded GROUP BY area
    UNION ALL
    SELECT 'segmento',                segmento,           count(*),        sum(target_ge50) FROM banded GROUP BY segmento
    UNION ALL
    SELECT 'UF',                      UF,                 count(*),        sum(target_ge50) FROM banded GROUP BY UF
    UNION ALL
    SELECT 'faixa_valor',             faixa_valor,        count(*),        sum(target_ge50) FROM banded GROUP BY faixa_valor
)
SELECT
    dimensao,
    valor,
    n,
    k AS reached_50pct,
    round(k::DOUBLE / n, 4) AS rate,
    -- Wilson score interval at 95%
    round((k + 1.920729) / (n + 3.841459)
          - 1.959964 / (n + 3.841459)
            * sqrt((k::DOUBLE * (n - k)) / n + 0.960365), 4) AS ci_low,
    round((k + 1.920729) / (n + 3.841459)
          + 1.959964 / (n + 3.841459)
            * sqrt((k::DOUBLE * (n - k)) / n + 0.960365), 4) AS ci_high
FROM by_dimension
WHERE n >= 30  -- cells thinner than this are not reported, they are noise
ORDER BY dimensao, rate DESC;
