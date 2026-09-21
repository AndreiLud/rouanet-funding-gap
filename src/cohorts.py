"""Classify a project's `situacao` into the fundraising window state.

This is the censoring decision, and it is the one that decides who is in the sample.
`situacao` is settled after the fact, so it is used here and never as a model feature.

Three states:

- `pre_approval`: still being evaluated, rejected, or never reached an authorisation to
  raise funds. These are not approved projects, so they are outside the question.
- `open`: authorised to raise and the window is still running, or an extension is
  pending. The outcome is not final, so including them would score them as failures.
- `closed`: the fundraising window has ended, whatever happened next. Only these are
  analysable.

Within `closed`, `withdrawn` marks projects the proponent or the ministry pulled out
rather than ones that ran their window to the end. Whether a withdrawal counts as a
funding failure is a judgement call, so it is carried as a flag and the headline result
is reported both ways.
"""
from __future__ import annotations

import re

# Matched in order. First hit wins, so the specific patterns come before the general.
RULES: list[tuple[str, str]] = [
    # Not approved, or still being decided.
    (r"^indeferido", "pre_approval"),
    (r"encaminhado a comissão de avaliação", "pre_approval"),
    (r"encaminhado para avaliação", "pre_approval"),
    (r"encaminhado para análise técnica", "pre_approval"),
    (r"análise de resposta de diligência", "pre_approval"),
    (r"finalização do processo de homologação", "pre_approval"),
    (r"verificação documental", "pre_approval"),
    (r"em avaliação documental", "pre_approval"),
    (r"prazo recursal", "pre_approval"),
    (r"^diligenciado - parecer técnico", "pre_approval"),
    (r"^diligenciado - comissão nacional", "pre_approval"),
    (r"pauta para avaliação da cnic", "pre_approval"),
    (r"^recurso$", "pre_approval"),
    (r"reanalisar enquadramento", "pre_approval"),
    (r"aguarda publicação de portaria$", "pre_approval"),
    (r"portaria de autorização para captação", "pre_approval"),

    # Authorised and still raising, or about to have the window changed.
    (r"^autorizada a captação", "open"),
    (r"portaria de prorrogação", "open"),
    (r"portaria de redução", "open"),
    (r"portaria de complementação", "open"),
    (r"liberado para adequação à realidade", "open"),
    (r"adequado à realidade de execução", "open"),
    (r"^diligenciado - readequação", "open"),
    (r"^projeto suspenso", "open"),

    # The window has ended.
    (r"excesso de prazo sem captação", "closed"),
    (r"expirado o prazo de captação", "closed"),
    (r"encerrado prazo de captação", "closed"),
    (r"insuficiência de captação", "closed"),
    (r"prestação de contas", "closed"),
    (r"^inadimplente", "closed"),
    (r"análise financeira", "closed"),
    (r"aguarda análise financeira", "closed"),
    (r"análise preditiva após comprovação", "closed"),
    (r"avaliação de resultados", "closed"),
    (r"aguarda revisão de resultados", "closed"),
    (r"^diligenciado - monitoramento", "closed"),
    (r"relatório cumprimento de objeto", "closed"),
    (r"^diligenciado - movimentação da conta", "closed"),
    (r"débito parcelado", "closed"),

    # Pulled out. Terminal, but not a window that ran its course.
    (r"^arquiv", "withdrawn"),
    (r"desistência do proponente", "withdrawn"),
    (r"solicitação de arquivamento", "withdrawn"),
]


def classify(situacao: str | None) -> str:
    """Return one of pre_approval, open, closed, withdrawn, or unmapped."""
    s = (situacao or "").strip().lower()
    if not s:
        return "unmapped"
    for pattern, state in RULES:
        if re.search(pattern, s):
            return state
    return "unmapped"


def window_state(situacao: str | None) -> str:
    """Collapse withdrawn into closed for the analysable-sample decision."""
    state = classify(situacao)
    return "closed" if state == "withdrawn" else state
