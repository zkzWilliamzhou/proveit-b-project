---
name: proveit-audit
description: Run a proveit claim audit and interpret VERIFIED, CONTRADICTED and UNVERIFIABLE verdicts. Use when checking a repository's README promises against its source, or when wiring proveit into CI.
---

# Run a proveit audit

## Before you start

Read `docs/CLAIM_ONTOLOGY.md`. A claim outside the nine kinds is not decided.
Read `docs/OUTPUT_SCHEMA.md` for the exit codes.

## Commands

```console
python3 -m proveit scan PATH --format json
python3 -m proveit check PATH --format json
python3 -m proveit diff LEFT RIGHT --format json
python3 -m proveit selftest
python3 -m proveit ontology --format json
```

## Read the result

- CONTRADICTED means positive Evidence exists. Open the file and line named in
  the verdict. Do not argue with the state before reading the Evidence.
- VERIFIED means no contradicting capability inside the declared scan scope,
  with full coverage. Read the limitations. It is not a proof about all inputs.
- UNVERIFIABLE means the tool could not decide. Check `scan_complete`, the
  Notes, and whether the sentence carries a qualifier.

## CI

Use exit code 1 as the gate. Add `--fail-unverifiable` when the policy requires
every claim to be decidable. Use `--format sarif` for GitHub code scanning.
Disclose any `--exclude` path in the pull request description; the report
prints it.

## Never

Never treat a lack of findings as proof. Never hide an exclusion. Never claim
the program is safe because proveit returned VERIFIED.
