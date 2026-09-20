# Conventions for this repository

Project: "Approved is not funded: who actually raises money through Brazil's Rouanet Law".
Read `docs/project_brief.md` before changing anything.

## Language
All repository content is in English: code, comments, docs, notebooks, commit messages,
figures, app copy. Source data is in Portuguese and field names from the SALIC API keep
their original spelling (`valor_aprovado`, `PRONAC`), because renaming them would break
traceability back to the source.

## Typography
Never use an em dash (U+2014) or an en dash (U+2013) in any text. Use a comma, a colon
or parentheses instead. This applies to prose, code comments, figure titles and commit
messages.

## Numbers
Every number that appears in the README, in a notebook narrative, in a figure or in the
app comes from code executed in this repository. Nothing is estimated, recalled or
carried over from an external article. If a number cannot be produced by running the
pipeline, it does not get written down.

## Data
- `data/raw/` is immutable and untracked. One file per API page, named with the
  collection date. Never edit a raw file: fix problems downstream.
- `data/interim/` and `data/processed/` are untracked build artifacts, rebuilt by `make`.
- Raw pages contain `cgccpf` (CPF or CNPJ). Nothing carrying a natural person's
  document number or name leaves `data/raw/`.

## LGPD
Proponents and sponsors that are natural persons (`tipo_pessoa` indicating pessoa
fisica) must not be identifiable in the repository, in figures or in the app. Identity
is replaced by a salted hash before anything reaches `data/processed/`, and the salt is
not committed. Concentration statistics are reported as aggregates, never as named
rankings of natural persons.

## Leakage
Only variables knowable at the moment of approval may enter a model. The exclusion list
and the reason for each exclusion live in `docs/data_dictionary.md`. Proponent history
features are computed from strictly earlier projects only. The test set is touched once.

## SQL
Analytical tables are built with DuckDB. One `.sql` file per question in `sql/`, named
after the question it answers, each runnable on its own against the processed data.

## Reproducibility
- Seeds are fixed and defined in one place (`src/config.py`).
- `requirements.txt` pins exact versions.
- `make all` reproduces the pipeline end to end from the raw pages.
- Collection is resumable: rerunning it must not duplicate or lose pages.

## Figures
Title states the finding, not the variable ("Approved is not funded", not "Funding by
area"). Source line in the footer, including the collection date. One series highlighted
in colour, everything else in grey.

## Git
Small commits, one per step, with descriptive messages. Do not configure git user name
or email in this repository.
