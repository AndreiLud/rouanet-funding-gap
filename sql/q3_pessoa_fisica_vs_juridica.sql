-- Who actually gets funded: individuals or organisations?
--
-- The API masks a natural person's document (values like '***000*****') and returns a
-- company's CNPJ in full, so the mask is what identifies a pessoa fisica. This was
-- checked against the `tipo_pessoa` field on the proponentes endpoint, where masking
-- and the declared type agree exactly.
--
-- This matters for the ministry rather than for the producer: it measures whether the
-- mechanism reaches individual artists or only organisations.

SELECT
    CASE WHEN proponente_pessoa_fisica THEN 'pessoa fisica' ELSE 'pessoa juridica' END AS tipo,
    count(*) AS projetos,
    round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_dos_projetos,
    round(avg(target_ge50), 4) AS taxa_ge50,
    round(avg(CASE WHEN share_raised <= 0 THEN 1 ELSE 0 END), 4) AS taxa_zero,
    round(sum(valor_captado) / 1e6, 1) AS captado_milhoes,
    round(100.0 * sum(valor_captado) / sum(sum(valor_captado)) OVER (), 1) AS pct_do_dinheiro,
    round(median(valor_solicitado), 0) AS mediana_solicitado
FROM analysable
GROUP BY proponente_pessoa_fisica
ORDER BY projetos DESC;
