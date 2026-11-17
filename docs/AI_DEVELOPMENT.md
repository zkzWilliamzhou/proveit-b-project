# AI-assisted development disclosure

Parts of this repository were drafted with AI assistance: the initial module
skeleton, the first documentation drafts, the research reports in
`third_party/research/` and the adversarial fixture ideas. A human manager
reviewed every part before it shipped.

## What was verified, not assumed

- Every claim in `README.md` is checked by `python3 -m proveit selftest` and
  by `python3 -m proveit check .`.
- Every README command in the demo section was executed and its output copied
  verbatim into the document.
- The 71-test suite in `tests/test_proveit.py` runs against the final tree.
- Twelve review rounds are recorded in `docs/REVIEW_LOG.md` with the exact
  findings and the commands that proved each fix. Rounds 10-12 were added
  after the first delivery, when further probing found three real false
  positives that the earlier rounds had missed.
- Research figures in `third_party/research/` are labelled as approximate or
  as "not verified"; none is presented as a measured star count guarantee.

## Review process

1. Generate a candidate.
2. Run the full suite and the self-audit.
3. Inspect security-sensitive output: paths, terminal escapes, Markdown
   injection, resource budgets, exit codes.
4. Reject low-quality or fabricated material and redo the round.
5. Record what was checked and what remains uncertain.

A passing test is evidence of behaviour, not evidence of correct intent. The
claim adjudicator follows the same rule: it refuses to treat a lack of
findings as proof.

## No star-count claim

`>105k stars` was the brief's ambition, not a promise. The adoption research
in `third_party/research/ADOPTION_PLAYBOOK.md` concludes that stars measure
attention, not usage, quality or safety, and that no feature reliably causes
adoption. This project targets a documented capability gap instead.
