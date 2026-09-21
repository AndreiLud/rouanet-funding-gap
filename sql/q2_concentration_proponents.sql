-- Sub-question 2: how concentrated is fundraising across proponents?
--
-- Proponents are identified by a salted hash, never by name, and the salt is not
-- committed. That is enough to count how concentrated the money is and not enough to
-- name anybody, which is what LGPD requires here: some proponents are natural persons.
--
-- Gini is computed from the Lorenz curve over proponents ordered by money raised.

WITH per_proponente AS (
    SELECT
        ano_projeto AS cohort,
        proponente_hash,
        sum(valor_captado) AS captado,
        count(*) AS projetos
    FROM analysable
    WHERE proponente_hash IS NOT NULL
    GROUP BY ano_projeto, proponente_hash
),
ranked AS (
    SELECT
        cohort,
        captado,
        row_number() OVER (PARTITION BY cohort ORDER BY captado) AS rn,
        count(*)     OVER (PARTITION BY cohort) AS n,
        sum(captado) OVER (PARTITION BY cohort) AS total
    FROM per_proponente
),
gini AS (
    SELECT
        cohort,
        n,
        total,
        -- Gini = (2 * sum(rank_i * x_i)) / (n * sum(x)) - (n + 1) / n
        round(2.0 * sum(rn * captado) / nullif(n * total, 0) - (n + 1.0) / n, 4) AS gini
    FROM ranked
    GROUP BY cohort, n, total
),
top_decile AS (
    SELECT
        cohort,
        round(sum(captado) FILTER (WHERE rn > n - ceil(n / 10.0))
              / nullif(total, 0), 4) AS top10pct_share
    FROM ranked
    GROUP BY cohort, total
)
SELECT
    g.cohort,
    g.n AS proponentes,
    round(g.total, 2) AS captado_total,
    t.top10pct_share,
    g.gini
FROM gini g
JOIN top_decile t USING (cohort)
ORDER BY g.cohort;
