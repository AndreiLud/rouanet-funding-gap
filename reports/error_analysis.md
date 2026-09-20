# Error analysis

Held out cohort 2022, n = 2,620, actual rate 0.437.

## The failure is the level, not the ranking

- model mean predicted probability: 0.767
- heuristic mean predicted probability: 0.426
- what actually happened: 0.437

The model prices the cohort far above what happened while still ordering it sensibly, which is why its PR-AUC beats the heuristic and its Brier score loses to it.

## Calibration on the held out cohort

Model:

|   bin |   n |   mean_pred |   actual |
|------:|----:|------------:|---------:|
|     0 | 262 |      0.2562 |   0.1756 |
|     1 | 262 |      0.5313 |   0.355  |
|     2 | 262 |      0.6812 |   0.3893 |
|     3 | 262 |      0.7677 |   0.355  |
|     4 | 262 |      0.8209 |   0.3855 |
|     5 | 262 |      0.8617 |   0.4389 |
|     6 | 262 |      0.8937 |   0.4504 |
|     7 | 262 |      0.9247 |   0.5878 |
|     8 | 262 |      0.9535 |   0.5954 |
|     9 | 262 |      0.977  |   0.6412 |

Heuristic:

|   bin |   n |   mean_pred |   actual |
|------:|----:|------------:|---------:|
|     0 | 263 |      0.1056 |   0.1331 |
|     1 | 273 |      0.2971 |   0.359  |
|     2 | 263 |      0.3393 |   0.4601 |
|     3 | 281 |      0.3857 |   0.4021 |
|     4 | 246 |      0.4154 |   0.4715 |
|     5 | 281 |      0.4534 |   0.4448 |
|     6 | 227 |      0.4748 |   0.5022 |
|     7 | 263 |      0.5242 |   0.4943 |
|     8 | 264 |      0.59   |   0.5568 |
|     9 | 259 |      0.6868 |   0.5676 |

## Feature drift between train and the held out cohort

| feature                   |   train_median |   test_median |   train_missing |   test_missing |
|:--------------------------|---------------:|--------------:|----------------:|---------------:|
| valor_solicitado_log      |          12.61 |         13.1  |           0     |          0     |
| outras_fontes_log         |           0    |          0    |           0     |          0     |
| n_municipios              |           1    |          1    |           0     |          0     |
| duracao_dias              |         852    |        514    |           0     |          0.001 |
| len_objetivos             |        1277    |       1990.5  |           0     |          0     |
| len_justificativa         |        2833    |       3078    |           0     |          0     |
| len_resumo                |         420    |        417    |           0     |          0     |
| len_ficha_tecnica         |        5027    |       4995    |           0     |          0     |
| len_etapa                 |        1023    |       1062    |           0     |          0     |
| len_democratizacao        |        1100.5  |       1242    |           0     |          0     |
| len_especificacao_tecnica |         489.5  |        660.5  |           0     |          0     |
| prior_projetos            |           2    |          2    |           0.772 |          0.542 |
| prior_taxa_ge50           |           0.6  |          0.88 |           0.772 |          0.542 |
| prior_captado_log         |          13.01 |         13.3  |           0.772 |          0.542 |

The proponent history features are the ones that matter here. Their missing rate falls as the observation window lengthens, and the observed prior success rate drifts upwards because proponents who appear repeatedly are disproportionately the ones who succeeded. The feature means something different in 2022 than it meant in 2020, which is a property of the window and not of the projects.

## Error by area

| area                |   n |   actual |   predicted |    gap |   brier |
|:--------------------|----:|---------:|------------:|-------:|--------:|
| Museus e Memoria    |  81 |   0.4691 |      0.8772 | 0.4081 |  0.3965 |
| Patrimonio Cultural |  88 |   0.3523 |      0.7425 | 0.3903 |  0.3954 |
| Humanidades         | 382 |   0.4084 |      0.762  | 0.3536 |  0.3766 |
| Musica              | 729 |   0.4019 |      0.7444 | 0.3425 |  0.3412 |
| Artes Cenicas       | 830 |   0.4639 |      0.7812 | 0.3174 |  0.3518 |
| Artes Visuais       | 273 |   0.4432 |      0.7525 | 0.3092 |  0.3465 |
| Audiovisual         | 237 |   0.5148 |      0.7805 | 0.2658 |  0.285  |

## Error by state

| UF   |   n |   actual |   predicted |    gap |   brier |
|:-----|----:|---------:|------------:|-------:|--------:|
| GO   |  53 |   0.1321 |      0.6316 | 0.4995 |  0.3696 |
| ES   |  56 |   0.3929 |      0.845  | 0.4522 |  0.4138 |
| MG   | 352 |   0.3693 |      0.7848 | 0.4155 |  0.4163 |
| BA   |  48 |   0.25   |      0.6487 | 0.3987 |  0.4253 |
| PR   | 208 |   0.4808 |      0.844  | 0.3633 |  0.3843 |
| PE   |  51 |   0.2941 |      0.6505 | 0.3563 |  0.2975 |
| SC   | 195 |   0.5077 |      0.833  | 0.3253 |  0.3529 |
| SP   | 793 |   0.4615 |      0.7821 | 0.3205 |  0.3464 |
| CE   |  72 |   0.5417 |      0.8505 | 0.3088 |  0.3498 |
| RS   | 263 |   0.5361 |      0.8185 | 0.2824 |  0.322  |
| RJ   | 315 |   0.4349 |      0.676  | 0.241  |  0.2693 |
| DF   |  52 |   0.3269 |      0.5311 | 0.2042 |  0.2681 |

## Error by value band

| faixa_valor   |    n |   actual |   predicted |    gap |   brier |
|:--------------|-----:|---------:|------------:|-------:|--------:|
| 100k to 500k  | 1658 |   0.38   |      0.7612 | 0.3812 |  0.3812 |
| 5M and above  |   95 |   0.4632 |      0.8318 | 0.3686 |  0.3937 |
| 1M to 5M      |  483 |   0.5362 |      0.7887 | 0.2525 |  0.2937 |
| 500k to 1M    |  322 |   0.5683 |      0.769  | 0.2007 |  0.2702 |
| under 100k    |   62 |   0.4839 |      0.6353 | 0.1514 |  0.2496 |

## Permutation importance on the held out cohort

Drop in PR-AUC when the feature is shuffled. This is association, not cause: none of these is a lever a producer can pull.

|                           |   drop_in_pr_auc |
|:--------------------------|-----------------:|
| prior_taxa_ge50           |           0.0469 |
| segmento                  |           0.0275 |
| prior_captado_log         |           0.0172 |
| prior_projetos            |           0.0159 |
| n_municipios              |           0.0135 |
| enquadramento             |           0.0113 |
| valor_solicitado_log      |           0.0054 |
| UF                        |           0.0052 |
| len_especificacao_tecnica |           0.0042 |
| len_ficha_tecnica         |           0.0017 |
| area                      |           0.0017 |
| tipologia                 |           0.0014 |
| len_objetivos             |           0.0005 |
| len_resumo                |           0.0002 |
| len_justificativa         |           0.0001 |
| mecanismo                 |           0      |
| outras_fontes_log         |          -0      |
| len_democratizacao        |          -0.0001 |
| len_etapa                 |          -0.0003 |
| duracao_dias              |          -0.007  |
| tipicidade                |          -0.016  |
