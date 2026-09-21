# Data quality report

Rows parsed: 61,337. Columns: 38.

## Identity

- Distinct PRONAC: 61,337
- Rows that share a PRONAC with another row: 0
- PRONACs appearing under more than one area code: 0


## Collection integrity

- area 1: 18,677 distinct PRONAC collected
- area 2: 6,301 distinct PRONAC collected
- area 3: 17,363 distinct PRONAC collected
- area 4: 6,776 distinct PRONAC collected
- area 5: 1,970 distinct PRONAC collected
- area 6: 8,722 distinct PRONAC collected
- area 7: 324 distinct PRONAC collected
- area 9: 1,204 distinct PRONAC collected


## Missing values

- `data_termino`: 328 (0.5%)
- `data_inicio`: 323 (0.5%)


## Impossible and suspicious values

- `valor_aprovado` negative: 36
- `valor_projeto` negative: 33
- approved projects (valor_aprovado > 0): 60,726
- captado above aprovado: 1,006 (1.7% of approved)
  - ratio median 1.00, max 335502438.5
  - above 2x approved: 33
- valor_aprovado == 0: 575
- valor_aprovado == 0 but valor_captado > 0: 18


## Categories

- distinct UF: 27 (outside the 27 federal units: none)
- distinct segmento: 123
- distinct area: 8
- distinct tipologia: 113
- distinct tipicidade: 18
- distinct mecanismo: 2
- distinct enquadramento: 3


## Cohort coverage

- 2016: 1 projects, 1 with valor_aprovado > 0
- 2018: 1 projects, 1 with valor_aprovado > 0
- 2019: 3,508 projects, 3,158 with valor_aprovado > 0
- 2020: 4,683 projects, 4,616 with valor_aprovado > 0
- 2021: 2,645 projects, 2,630 with valor_aprovado > 0
- 2022: 2,681 projects, 2,670 with valor_aprovado > 0
- 2023: 10,722 projects, 10,681 with valor_aprovado > 0
- 2024: 14,215 projects, 14,190 with valor_aprovado > 0
- 2025: 15,415 projects, 15,384 with valor_aprovado > 0
- 2026: 7,466 projects, 7,395 with valor_aprovado > 0


## Situacao values (66 distinct)

- 18,272  Autorizada a captação total dos recursos
- 17,309  Projeto encerrado por excesso de prazo sem captação 
- 8,735  Apresentou prestação de contas
- 5,032  Autorizada a captação residual dos recursos
- 2,394  Arquivado - solicitação de desistência do proponente
- 1,894  Arquivado
- 1,055  Expirado o prazo de captação total
- 961  Arquivado a pedido proponente
- 942  Projeto não executado por insuficiência de captação de recursos
- 699  Indeferido
- 432  Projeto em execução - Encerrado prazo de captação
- 415  Projeto liberado para adequação à realidade de execução.
- 361  Prestação de Contas Aprovada
- 283  Expirado o prazo de captação parcial
- 267  Análise Financeira da Prestação de Contas
- 213  Edital - Encaminhado a Comissão de Avaliação
- 173  Iniciado prazo para apresentar prestação de contas
- 172  Arquivado - não atendimento à diligência técnica
- 169  Prestação de contas desaprovada com INDICATIVO para Tomada de Contas Especial
- 156  Encaminhado para análise técnica
- 125  Análise de resposta de diligência - Objeto
- 114  Projeto encaminhado para finalização do processo de homologação
- 109  Projeto de edital - encaminhado para avaliação
- 98  Projeto suspenso
- 88  Projeto apreciado pela Comissão Nacional de Incentivo à Cultura - CNIC. Projeto em verificação documental.
- 86  Inadimplente
- 81  Em análise técnica (avaliação de resultados)
- 71  Análise de resposta de diligência
- 59  Aguardando superação/desistência do prazo recursal
- 59  Apresentou prestação de contas após reprovação
- 49  Prestação de contas aprovada com ressalva formal e sem prejuízo
- 45  Diligenciado - Parecer técnico
- 37  Projeto adequado à realidade de execução
- 34  Análise preditiva após comprovação
- 33  Projeto incluído em pauta para avaliação da CNIC
- 32  Projeto em avaliação documental
- 31  Indeferido - projeto em duplicidade
- 23  Análise de recurso prestação de contas
- 20  Aguarda publicação de portaria de Prorrogação
- 20  Diligenciado - na avaliação do relatório cumprimento de objeto
- 19  Aguarda elaboração de portaria de Prorrogação
- 18  Encaminhado para inclusão em portaria de autorização para captação de recursos
- 16  Inadimplente - por não responder diligência na avaliação do relatório cumprimento de objeto
- 15  Diligenciado - Comissão Nacional de Incentivo à Cultura - CNIC
- 14  Aguarda publicação de portaria
- 14  Recurso
- 13  Indeferido por não atender aos objetivos e finalidades da Lei 8313/91.
- 9  Diligenciado - Readequação
- 8  Prorrogado o prazo para apresentar prestação de contas
- 8  Diligenciado - Prestação de Contas
- 7  Inadimplente - Não atendeu a notificação para apresentar prestação de contas
- 6  Diligenciado - Monitoramento
- 6  Inadimplente - por não responder a diligência de monitoramento
- 6  Aguarda análise financeira
- 4  Inadimplente - não respondeu a diligência da Prestação de Contas
- 4  Prestação de contas desaprovada com notificação de cobrança
- 4  Arquivamento provisório por Prescrição - BAP TCU
- 4  Diligenciado - movimentação da conta corrente
- 3  Encaminhado para inclusão em portaria de redução.
- 2  Indeferido - Projeto já realizado.
- 2  Encaminhado para inclusão em portaria de complementação
- 2  Prestação de contas aprovada após ressarcimento ao erário.
- 2  Reanalisar enquadramento
- 1  Débito Parcelado
- 1  Solicitação de arquivamento feito pelo proponente
- 1  Aguarda revisão de resultados


## Fundraising window by cohort

- situacao values that no rule matched: 0

| cohort | closed | open | withdrawn | pre_approval | total | % open |
| --- | --- | --- | --- | --- | --- | --- |
| 2016 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| 2018 | 0 | 0 | 1 | 0 | 1 | 0.0 |
| 2019 | 2,807 | 2 | 217 | 482 | 3,508 | 0.1 |
| 2020 | 4,132 | 4 | 408 | 139 | 4,683 | 0.1 |
| 2021 | 2,424 | 7 | 188 | 26 | 2,645 | 0.3 |
| 2022 | 2,452 | 30 | 178 | 21 | 2,681 | 1.1 |
| 2023 | 6,240 | 2,932 | 1,305 | 245 | 10,722 | 27.3 |
| 2024 | 8,807 | 3,191 | 1,899 | 318 | 14,215 | 22.4 |
| 2025 | 3,171 | 10,995 | 995 | 254 | 15,415 | 71.3 |
| 2026 | 117 | 6,746 | 235 | 368 | 7,466 | 90.4 |


## Outcome by cohort (closed window, valor_aprovado > 0)

| cohort | n | raised >0% | >=20% | >=50% | >=100% |
| --- | --- | --- | --- | --- | --- |
| 2016 | 1 | 100.0% | 100.0% | 100.0% | 0.0% |
| 2018 | 1 | 100.0% | 0.0% | 0.0% | 0.0% |
| 2019 | 3,016 | 51.0% | 47.2% | 38.6% | 6.4% |
| 2020 | 4,489 | 44.4% | 41.9% | 36.6% | 6.7% |
| 2021 | 2,597 | 49.6% | 47.1% | 42.6% | 7.1% |
| 2022 | 2,620 | 58.9% | 54.9% | 44.2% | 6.1% |
| 2023 | 7,517 | 39.0% | 33.2% | 24.1% | 3.4% |
| 2024 | 10,693 | 19.7% | 14.8% | 10.6% | 2.5% |
| 2025 | 4,140 | 15.2% | 11.4% | 8.5% | 3.0% |
| 2026 | 314 | 4.5% | 2.2% | 0.6% | 0.0% |

A cohort with a high share still open cannot be read from this table: the projects that close first are disproportionately the ones that closed for raising nothing, so a partially open cohort understates the rate. Only cohorts that are essentially fully closed are usable.
