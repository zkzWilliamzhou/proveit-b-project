# ADR-0003: one pipeline module behind the FileView seam

Status: accepted. Applied in review round 7.

## Context

`cli.collect` and `selftest.run` both performed walk, scan, manifest attach,
claim extraction and adjudication. Three CLI call sites plus the self-audit
meant four copies of the same ordering. A coverage fix in one copy could be
forgotten in another. The interface was as wide as the implementation, which
is the definition of a shallow module.

## Decision

`proveit/pipeline.py` owns the sequence. `read_tree` returns
`(Receipt, license_fact, claims)`; `audit_tree` adds adjudication. `cli.collect`
and `selftest.run` became thin wrappers. `model.Receipt` gained
`with_manifests` and `with_notes` so record construction is concentrated and
`scan_complete` is recomputed when a warning Note arrives.

The seam is the `FileView` list from `workspace.walk`. Two adapters already
exist behind it: the real filesystem walk and the in-memory views used by
tests. One adapter would be hypothetical; two make it real.

## Consequences

- One place to test for coverage, ordering and budget behaviour.
- A new manifest parser or claim kind slots in without touching the CLI.
- No behaviour changed. Round 7 of `docs/REVIEW_LOG.md` records golden
  outputs before and after.

## Revisit trigger

A second execution mode (for example a git-commit adapter) appears. Add it as
a new Adapter behind the same seam; do not fork `read_tree`.
