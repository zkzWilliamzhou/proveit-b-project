# Contributing

## Before you open a pull request

1. Run `python3 -m unittest discover -s tests -v`.
2. Run `python3 -m proveit selftest`.
3. Run `python3 -m proveit check . --format json` and confirm zero
   CONTRADICTED claims.
4. If you changed a rule, a claim kind or a verdict reason, update
   `docs/CLAIM_ONTOLOGY.md`, `docs/OUTPUT_SCHEMA.md` and the README demo
   output. The demos are verbatim tool output; keep them that way.
5. Add a test that covers both the positive and the negative case.

## Rule changes

`proveit/rules.py` is frozen data. It contains lowercase literals only. Do
not add a regular expression, and do not let a scanned repository supply a
pattern. A new capability needs a rule id, a scope, a description, an entry
in `NEGATIVE_REQUIREMENTS` when it can contradict a claim, and a test that
uses assembled string pieces so the test file itself stays clean.

## Verdict changes

`adjudicator.py` is a pure function of a Claim and a Receipt. CONTRADICTED
must always carry Evidence. VERIFIED for a negative claim must require
`scan_complete`. Never turn missing evidence into proof.

## Output changes

Any JSON field change bumps `schema_version`. Output must stay deterministic:
no timestamps, no absolute paths, no random values, sorted collections. All
repository-derived strings pass through `sanitize.py` before rendering.

## Scope

`third_party/` holds vendored skill catalogues, research reports and example
fixtures. It is outside the declared scan scope. Do not move project source
there to make a claim pass.

Read `docs/REVIEW_LOG.md` for the twelve review rounds and their residual risks.
Round 10 is required reading before touching `scanner.py` or `rules.py`:
capability names inside string literals, inline comments and docstrings are
data, and a masked first occurrence must not hide a real call later on the
same line.
`docs/adr/` records the decisions that should not be re-litigated without a
new ADR.
