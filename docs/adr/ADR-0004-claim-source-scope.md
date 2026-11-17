# ADR-0004: claim sources are root-level promise documents

Status: accepted.

## Context

The first implementation read claims from every Markdown file. On this
repository that produced 120 CONTRADICTED verdicts from quoted research
notes, third-party skill READMEs and changelog fragments that were never
promises made by `proveit`. A tool that accuses a project of lying because a
quoted sentence appears in a research appendix is not trustworthy.

## Decision

Default claim sources are root-level `README*`, `SECURITY*`, `PRIVACY*` and
`CONTRIBUTING*` documents. Fenced code, block quotes and table rows inside
them are skipped. `--claim-docs` widens reading to Markdown under `docs/`.
Vendored material lives in `third_party/` and is outside scan scope by
design. Root-level manifests and LICENSE files decide dependency and license
claims; nested copies do not describe the project as a whole.

## Consequences

- Quoted material stops generating false claims.
- Projects that put promises in `docs/` must pass `--claim-docs`; the flag is
  documented in the README.
- A nested manifest cannot accidentally decide a root claim.
- Exclusions and excluded directories appear as Notes and in every verdict's
  limitations.

## Revisit trigger

A maintained standard for machine-readable claim files (a `CLAIMS.toml` or a
signed behaviour manifest) becomes common. Add it as a new claim source with
its own parser; keep prose reading bounded.
