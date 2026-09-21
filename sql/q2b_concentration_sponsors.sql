-- Sub-question 2, sponsor side: how concentrated is the money that comes in?
--
-- Scope warning: `total_doado` is a lifetime total per sponsor with no date attached,
-- so this is a cross section over the whole history the API exposes, NOT the 2019 to
-- 2022 window the rest of the analysis uses. A per year series would need the
-- donations endpoint for every one of the 113,757 sponsors, which is a far heavier
-- pull. The limitation is stated rather than patched with a biased sample of the
-- largest sponsors, which would overstate concentration by construction.
--
-- Sponsors are identified by a salted hash. Most of them are natural persons.

WITH ranked AS (
    SELECT
        total_doado,
        tipo_pessoa,
        row_number() OVER (ORDER BY total_doado) AS rn,
        count(*)     OVER () AS n,
        sum(total_doado) OVER () AS total
    FROM incentivadores
    WHERE total_doado > 0
)
SELECT
    n AS incentivadores,
    round(total / 1e9, 2) AS total_doado_bilhoes,
    round(sum(total_doado) FILTER (WHERE rn > n - ceil(n / 10.0)) / total, 4) AS top10pct_share,
    round(sum(total_doado) FILTER (WHERE rn > n - ceil(n / 100.0)) / total, 4) AS top1pct_share,
    round(2.0 * sum(rn * total_doado) / (n * total) - (n + 1.0) / n, 4) AS gini,
    round(sum(total_doado) FILTER (WHERE tipo_pessoa = 'juridica') / total, 4) AS share_from_companies,
    count(*) FILTER (WHERE tipo_pessoa = 'fisica') AS n_pessoa_fisica
FROM ranked
GROUP BY n, total;
