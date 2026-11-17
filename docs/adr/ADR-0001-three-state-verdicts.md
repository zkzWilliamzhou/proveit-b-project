# ADR-0001: three-state verdicts, absence is not proof

Status: accepted.

## Context

A documentation claim auditor can fail in two opposite ways. It can call
everything a lie, or it can call everything verified. Both are worthless in
CI. A binary pass/fail gives no place to put "I could not check this", and a
confidence score invites users to treat 0.8 as proof.

## Decision

Every Claim resolves to VERIFIED, CONTRADICTED or UNVERIFIABLE. CONTRADICTED
requires positive Evidence. VERIFIED for a negative claim requires a complete
scan. UNVERIFIABLE is a normal outcome, not an error, and carries reasons.

A qualifier on the sentence, an incomplete scan, a missing manifest, a
skipped file, or a claim about binary assets all produce UNVERIFIABLE.

## Consequences

- CI can fail on CONTRADICTED without drowning in UNVERIFIABLE noise.
- `--fail-unverifiable` exists for teams that want the stricter gate.
- Every verdict must print limitations. A VERIFIED result is scoped, not
  absolute.
- The tool will sometimes look less impressive than a scanner that says
  "VERIFIED" for everything. That is the point.

## Revisit trigger

A user needs a fourth state that cannot be expressed as a limitation on one
of these three. Do not add a numeric confidence field.
